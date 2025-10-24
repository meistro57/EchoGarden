# api/main.py
"""FastAPI application exposing EchoGarden's service surface."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
import json
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple
import zipfile

import click
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, execute_batch
import tiktoken

from services import (
    TopicBundle,
    build_highlights,
    extract_topics,
    normalize_message,
    parse_search_terms,
    redact_text,
)

app = FastAPI(title="MCP Chat Log Intelligence API", version="0.3.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # UI origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


class ContextPackRequest(BaseModel):
    """Request body for building conversational context packs."""

    message_ids: List[str] = Field(default_factory=list, description="Ordered list of conversation/message identifiers")
    max_tokens: int = Field(6000, gt=0, le=16384, description="Maximum tokens to include in the pack")
    model: str = Field("gpt-4", description="Model name used to derive token encoding")

    @validator("message_ids", each_item=True)
    def validate_message_id(cls, value: str) -> str:
        if "/" not in value:
            raise ValueError("Message identifiers must be in the form '<conversation>/<message>'")
        return value


class ContextPackResponse(BaseModel):
    """Response describing the constructed context pack."""

    text_block: str
    token_count: int
    message_count: int


class ConversationSummary(BaseModel):
    """Summary metadata for a stored conversation."""

    conv_id: str
    title: str
    owner_id: str
    message_count: int
    first_message_ts: Optional[str]
    last_message_ts: Optional[str]


class ConversationListResponse(BaseModel):
    """Paginated list response for conversations."""

    items: List[ConversationSummary]
    total: int
    limit: int
    offset: int


class ConversationStats(BaseModel):
    """Aggregate statistics for a single conversation."""

    conv_id: str
    message_count: int
    participant_roles: List[str]
    first_message_ts: Optional[str]
    last_message_ts: Optional[str]
    average_message_length: float


class ThreadMessage(BaseModel):
    """Representation of a message node when exploring a thread."""

    msg_id: str
    parent_id: Optional[str]
    role: str
    ts: str
    text: str


class ThreadResponse(BaseModel):
    """Tree payload for an anchored message and its neighbours."""

    anchor: ThreadMessage
    ancestors: List[ThreadMessage]
    descendants: List[ThreadMessage]


class TopicAnchor(BaseModel):
    """Description of a representative message for a topic."""

    conv_id: str
    msg_id: str
    role: Optional[str]
    ts: Optional[str]
    text: str


class TopicEntry(BaseModel):
    """Serializable representation of a derived topic."""

    label: str
    occurrences: int
    weight: float
    first_seen_ts: Optional[str]
    anchors: List[TopicAnchor]


class TopicMapResponse(BaseModel):
    """Response payload summarising topics over a time window."""

    topics: List[TopicEntry]
    total_messages: int
    distinct_conversations: int
    window_start: Optional[str]
    window_end: Optional[str]


# Database connection helpers

def get_db() -> psycopg2.extensions.connection:
    """Create a new PostgreSQL connection using the configured DSN."""

    return psycopg2.connect(
        dsn=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    )


@contextmanager
def db_cursor(*, dict_cursor: bool = False) -> Iterable[Tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]]:
    """Context manager that yields a cursor and ensures cleanup."""

    conn = get_db()
    cursor_factory = RealDictCursor if dict_cursor else None
    cur = conn.cursor(cursor_factory=cursor_factory)
    try:
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def _normalise_iso(value: Optional[str]) -> Optional[str]:
    """Validate and normalise ISO-8601 timestamps."""

    if value is None:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:  # pragma: no cover - defensive guard for invalid dates
        raise HTTPException(status_code=400, detail=f"Invalid ISO timestamp: {value}") from exc
    return candidate


# Import ChatGPT export
@app.post("/ingest/chatgpt-export")
def ingest_chatgpt_export(zip_path: str, owner_id: str = "default") -> Dict[str, Any]:
    with db_cursor() as (conn, cur):
        try:
            click.echo(f"Opening {zip_path}...")
            with zipfile.ZipFile(zip_path, "r") as archive:
                with archive.open("conversations.json") as handle:
                    conversations = json.load(handle)

            total_imported = 0
            conv_count = 0

            for conv_data in conversations:
                conv_id = conv_data["id"]
                title = conv_data.get("title", "Untitled")

                cur.execute(
                    """
                    INSERT INTO conversations (conv_id, title, owner_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (conv_id) DO UPDATE SET title = EXCLUDED.title
                    """,
                    (conv_id, title, owner_id),
                )

                conv_count += 1

                messages: List[Tuple[str, str, str, str, str, Optional[str], str, str]] = []
                for msg_id, msg_data in conv_data.get("mapping", {}).items():
                    message_payload = msg_data.get("message")
                    if not message_payload:
                        continue

                    message_payload["id"] = msg_id
                    normalised = normalize_message(message_payload, conv_id, owner_id)
                    messages.append(
                        (
                            normalised["conv_id"],
                            normalised["msg_id"],
                            normalised["role"],
                            normalised["ts"],
                            normalised["text"],
                            normalised.get("parent_id"),
                            normalised["hash"],
                            json.dumps(normalised["meta"]),
                        )
                    )

                if messages:
                    execute_batch(
                        cur,
                        """
                        INSERT INTO messages
                        (conv_id, msg_id, role, ts, text, parent_id, hash, meta)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (conv_id, msg_id) DO NOTHING
                        """,
                        messages,
                    )
                    total_imported += len(messages)

            return {"imported": total_imported, "conversations": conv_count}
        except zipfile.BadZipFile as exc:
            raise HTTPException(status_code=400, detail=f"Invalid zip archive: {exc}") from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive safety net
            raise HTTPException(status_code=500, detail=f"Import failed: {exc}") from exc


@app.get("/health")
def health() -> Dict[str, Any]:
    try:
        with db_cursor() as (_, cur):
            cur.execute("SELECT 1;")
        return {"status": "healthy", "version": app.version}
    except Exception:
        return {"status": "unhealthy"}


@app.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    owner_id: Optional[str] = Query(None, description="Filter conversations by owner"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ConversationListResponse:
    with db_cursor(dict_cursor=True) as (_, cur):
        filters: List[str] = []
        params: List[Any] = []
        if owner_id:
            filters.append("owner_id = %s")
            params.append(owner_id)

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        count_query = sql.SQL("SELECT COUNT(*) FROM conversations {where_clause}").format(
            where_clause=sql.SQL(where_clause)
        )
        cur.execute(count_query, params)
        count_row = cur.fetchone()
        total = int(count_row["count"]) if count_row else 0

        data_query = sql.SQL(
            """
            SELECT
                c.conv_id,
                c.title,
                c.owner_id,
                COALESCE(COUNT(m.msg_id), 0) AS message_count,
                MIN(m.ts)::text AS first_message_ts,
                MAX(m.ts)::text AS last_message_ts
            FROM conversations c
            LEFT JOIN messages m ON c.conv_id = m.conv_id
            {where_clause}
            GROUP BY c.conv_id, c.title, c.owner_id
            ORDER BY last_message_ts DESC NULLS LAST, c.title ASC
            LIMIT %s OFFSET %s
            """
        ).format(where_clause=sql.SQL(where_clause))

        cur.execute(data_query, [*params, limit, offset])
        items = [ConversationSummary(**row) for row in cur.fetchall()]

    return ConversationListResponse(items=items, total=total, limit=limit, offset=offset)


@app.get("/conversation/{conv_id}/stats", response_model=ConversationStats)
def get_conversation_stats(conv_id: str) -> ConversationStats:
    with db_cursor(dict_cursor=True) as (_, cur):
        cur.execute(
            """
            SELECT
                COUNT(*) AS message_count,
                ARRAY(SELECT DISTINCT role FROM messages WHERE conv_id = %s) AS roles,
                MIN(ts)::text AS first_message_ts,
                MAX(ts)::text AS last_message_ts,
                COALESCE(AVG(LENGTH(text)), 0) AS avg_length
            FROM messages
            WHERE conv_id = %s
            """,
            (conv_id, conv_id),
        )
        row = cur.fetchone()
        if row is None or row["message_count"] == 0:
            raise HTTPException(status_code=404, detail="Conversation not found or empty")

    return ConversationStats(
        conv_id=conv_id,
        message_count=int(row["message_count"]),
        participant_roles=sorted(filter(None, row["roles"] or [])),
        first_message_ts=row["first_message_ts"],
        last_message_ts=row["last_message_ts"],
        average_message_length=float(row["avg_length"]),
    )


@app.get("/conversation/{conv_id}/timeline")
def get_timeline(conv_id: str) -> Dict[str, Any]:
    with db_cursor(dict_cursor=True) as (_, cur):
        cur.execute(
            """
            SELECT conv_id, msg_id, role, ts::text, text, parent_id, meta
            FROM messages
            WHERE conv_id = %s
            ORDER BY ts ASC
            """,
            (conv_id,),
        )
        messages = cur.fetchall()
    return {"messages": messages}


@app.get("/conversation/{conv_id}/thread/{msg_id}", response_model=ThreadResponse)
def get_thread(
    conv_id: str,
    msg_id: str,
    depth: int = Query(3, ge=1, le=10, description="Maximum descendant depth to traverse"),
) -> ThreadResponse:
    with db_cursor(dict_cursor=True) as (_, cur):
        cur.execute(
            """
            SELECT msg_id, parent_id, role, ts::text, text
            FROM messages
            WHERE conv_id = %s
            """,
            (conv_id,),
        )
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages_by_id: Dict[str, ThreadMessage] = {
        row["msg_id"]: ThreadMessage(**row) for row in rows
    }
    if msg_id not in messages_by_id:
        raise HTTPException(status_code=404, detail="Message not found in conversation")

    children_index: Dict[Optional[str], List[ThreadMessage]] = {}
    for message in messages_by_id.values():
        children_index.setdefault(message.parent_id, []).append(message)

    for siblings in children_index.values():
        siblings.sort(key=lambda item: item.ts)

    anchor = messages_by_id[msg_id]

    ancestors: List[ThreadMessage] = []
    current_parent = anchor.parent_id
    while current_parent:
        parent_message = messages_by_id.get(current_parent)
        if not parent_message:
            break
        ancestors.append(parent_message)
        current_parent = parent_message.parent_id
    ancestors.reverse()

    def gather_descendants(node_id: str, current_depth: int) -> List[ThreadMessage]:
        if current_depth >= depth:
            return []
        result: List[ThreadMessage] = []
        for child in children_index.get(node_id, []):
            result.append(child)
            result.extend(gather_descendants(child.msg_id, current_depth + 1))
        return result

    descendants = gather_descendants(anchor.msg_id, 0)

    return ThreadResponse(anchor=anchor, ancestors=ancestors, descendants=descendants)


@app.get("/search")
def search_messages(q: str, k: int = 50, filters: Optional[str] = None) -> Dict[str, Any]:
    with db_cursor(dict_cursor=True) as (_, cur):
        filter_dict = json.loads(filters) if filters else {}

        where_parts: List[str] = []
        params: List[Any] = []

        if "role" in filter_dict:
            where_parts.append(f"role = %s")
            params.append(filter_dict["role"])

        if "conv_id" in filter_dict:
            where_parts.append(f"conv_id = %s")
            params.append(filter_dict["conv_id"])

        if "date_from" in filter_dict:
            where_parts.append(f"ts >= %s")
            params.append(filter_dict["date_from"])

        if "date_to" in filter_dict:
            where_parts.append(f"ts <= %s")
            params.append(filter_dict["date_to"])

        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

        terms = parse_search_terms(q)
        if not terms:
            raise HTTPException(status_code=400, detail="Search query must contain at least one term")

        search_terms = " | ".join(terms)

        query = sql.SQL(
            """
            SELECT
                conv_id,
                msg_id,
                role,
                ts::text,
                LEFT(text, 400) AS snippet,
                ts_rank_cd(to_tsvector('english', text), to_tsquery('english', %s)) AS score
            FROM messages
            {where_clause}
            ORDER BY score DESC NULLS LAST
            LIMIT %s
            """
        ).format(where_clause=sql.SQL(where_clause))

        cur.execute(query, [*params, search_terms, k])
        results = cur.fetchall()

    hits: List[Dict[str, Any]] = []
    for row in results:
        highlights = build_highlights(row.get("snippet", ""), terms)
        hits.append(
            {
                "conv_id": row["conv_id"],
                "msg_id": row["msg_id"],
                "role": row["role"],
                "ts": row["ts"],
                "text": row["snippet"],
                "score": float(row["score"] or 0.0),
                "highlights": highlights,
            }
        )

    return {"results": hits, "total": len(hits)}


@app.get("/analytics/topic-map", response_model=TopicMapResponse)
def build_topic_map(
    date_from: Optional[str] = Query(None, description="Inclusive ISO-8601 timestamp filter"),
    date_to: Optional[str] = Query(None, description="Inclusive ISO-8601 timestamp filter"),
    conv_id: Optional[str] = Query(None, description="Restrict to a specific conversation"),
    limit: int = Query(10, ge=1, le=50, description="Number of topic labels to return"),
    min_occurrences: int = Query(2, ge=1, le=20, description="Minimum messages required for a topic"),
    sample_limit: int = Query(3, ge=1, le=5, description="Sample anchors retained per topic"),
    max_messages: int = Query(5000, ge=10, le=20000, description="Maximum messages scanned for the window"),
) -> TopicMapResponse:
    start_ts = _normalise_iso(date_from)
    end_ts = _normalise_iso(date_to)

    with db_cursor(dict_cursor=True) as (_, cur):
        where_parts: List[str] = []
        params: List[Any] = []

        if conv_id:
            where_parts.append("conv_id = %s")
            params.append(conv_id)
        if start_ts:
            where_parts.append("ts >= %s")
            params.append(start_ts)
        if end_ts:
            where_parts.append("ts <= %s")
            params.append(end_ts)

        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

        query = sql.SQL(
            """
            SELECT conv_id, msg_id, role, ts::text AS ts, text
            FROM messages
            {where_clause}
            ORDER BY ts ASC
            LIMIT %s
            """
        ).format(where_clause=sql.SQL(where_clause))

        cur.execute(query, [*params, max_messages])
        rows = cur.fetchall()

    if not rows:
        return TopicMapResponse(
            topics=[],
            total_messages=0,
            distinct_conversations=0,
            window_start=start_ts,
            window_end=end_ts,
        )

    topic_bundles: List[TopicBundle] = extract_topics(
        rows,
        limit=limit,
        min_occurrences=min_occurrences,
        sample_limit=sample_limit,
    )

    topics: List[TopicEntry] = []
    for bundle in topic_bundles:
        anchors = [
            TopicAnchor(
                conv_id=sample.conv_id,
                msg_id=sample.msg_id,
                role=sample.role,
                ts=sample.ts,
                text=sample.text,
            )
            for sample in bundle.anchors
        ]
        topics.append(
            TopicEntry(
                label=bundle.label,
                occurrences=bundle.occurrences,
                weight=bundle.weight,
                first_seen_ts=bundle.first_seen_ts,
                anchors=anchors,
            )
        )

    distinct_conversations = len({row["conv_id"] for row in rows})

    return TopicMapResponse(
        topics=topics,
        total_messages=len(rows),
        distinct_conversations=distinct_conversations,
        window_start=rows[0].get("ts"),
        window_end=rows[-1].get("ts"),
    )


@app.post("/context/pack", response_model=ContextPackResponse)
def build_context_pack(request: ContextPackRequest) -> ContextPackResponse:
    if not request.message_ids:
        return ContextPackResponse(text_block="", token_count=0, message_count=0)

    with db_cursor(dict_cursor=True) as (_, cur):
        conv_ids, msg_ids = zip(*[identifier.split("/", 1) for identifier in request.message_ids])
        cur.execute(
            """
            SELECT msg_id, role, ts::text, text
            FROM messages
            WHERE conv_id = ANY(%s) AND msg_id = ANY(%s)
            ORDER BY ts ASC
            """,
            (list(conv_ids), list(msg_ids)),
        )
        messages = cur.fetchall()

    try:
        encoding = tiktoken.encoding_for_model(request.model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    context_parts: List[str] = []
    current_tokens = 0
    for message in messages:
        formatted = f"[{message['role']} • {message['ts'][:16]}] {message['text']}"
        token_length = len(encoding.encode(formatted))
        if current_tokens + token_length > request.max_tokens:
            break
        context_parts.append(formatted)
        current_tokens += token_length

    text_block = "\n\n".join(context_parts)
    if len(messages) > len(context_parts):
        text_block += f"\n\n-- Truncated at {request.max_tokens} tokens --"

    return ContextPackResponse(
        text_block=text_block,
        token_count=current_tokens,
        message_count=len(context_parts),
    )


@app.post("/redact")
def redact_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = payload.get("text", "")
    enable_pii = payload.get("enable_pii", True)
    return {"text": redact_text(text, enable_pii=enable_pii)}


__all__ = ["app"]
