# api/main.py
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

import boto3
from botocore.client import Config
import click
from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from pydantic import BaseModel
import tiktoken
from typing import Any, Dict, List, Optional

from api.services import normalize_message, redact_text

app = FastAPI(title="MCP Chat Log Intelligence API", version="0.1.0")

# Database connection
def get_db():
    return psycopg2.connect(
        dsn=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    )

# Import ChatGPT export
@app.post("/ingest/chatgpt-export")
def ingest_chatgpt_export(zip_path: str, owner_id: str = "default"):
    conn = get_db()
    cur = conn.cursor()
    
    try:
        click.echo(f"Opening {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            with zf.open('conversations.json') as f:
                conversations = json.load(f)
        
        total_imported = 0
        conv_count = 0
        
        # Filter out any existing conversations to avoid duplicates
        
        for conv_data in conversations:
            conv_id = conv_data['id']
            title = conv_data.get('title', 'Untitled')
            
            # Insert conversation if not exists
            cur.execute("""
                INSERT INTO conversations (conv_id, title, owner_id) 
                VALUES (%s, %s, %s)
                ON CONFLICT (conv_id) DO UPDATE SET title = EXCLUDED.title
            """, (conv_id, title, owner_id))
            
            conv_count += 1
            
            # Collect messages for batch insert
            messages = []
            for msg_id, msg_data in conv_data.get('mapping', {}).items():
                if 'message' in msg_data and msg_data['message']:
                    msg = msg_data['message']
                    msg['id'] = msg_id  # Ensure ID is set
                    
                    normalized = normalize_message(msg, conv_id, owner_id)
                    messages.append((
                        normalized['conv_id'], normalized['msg_id'], normalized['role'],
                        normalized['ts'], normalized['text'], normalized.get('parent_id'), 
                        normalized['hash'], json.dumps(normalized['meta'])
                    ))
            
            if messages:
                # Batch upsert messages
                execute_batch(cur, """
                    INSERT INTO messages 
                    (conv_id, msg_id, role, ts, text, parent_id, hash, meta)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (conv_id, msg_id) DO NOTHING
                """, messages)
                total_imported += len(messages)
        
        conn.commit()
        return {"imported": total_imported, "conversations": conv_count}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/health")
def health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        return {"status": "healthy", "version": "0.1.0"}
    except:
        return {"status": "unhealthy"}

# Search messages with filters
@app.get("/search")
def search_messages(q: str, k: int = 50, filters: Optional[str] = None):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Parse filters
        filter_dict = json.loads(filters) if filters else {}
        
        # Build WHERE clause
        where_parts = []
        params = []
        
        if 'role' in filter_dict:
            where_parts.append(f"role = ${len(params)+1}")
            params.append(filter_dict['role'])
        
        if 'conv_id' in filter_dict:
            where_parts.append(f"conv_id = ${len(params)+1}")
            params.append(filter_dict['conv_id'])
        
        if 'date_from' in filter_dict or 'date_to' in filter_dict:
            if 'date_from' in filter_dict:
                where_parts.append(f"ts >= ${len(params)+1}")
                params.append(filter_dict['date_from'])
            if 'date_to' in filter_dict:
                where_parts.append(f"ts <= ${len(params)+1}")
                params.append(filter_dict['date_to'])
        
        where_clause = " AND ".join(where_parts)
        if where_clause:
            where_clause = f"WHERE {where_clause}"
        
        # Full-text search with ranking
        query = f"""
            SELECT 
                conv_id, msg_id, role, ts::text, left(text, 300) as snippet,
                ts_rank_cd(to_tsvector('english', text), to_tsquery('english', ${{len(params)+1}})) as score
            FROM messages
            {where_clause}
            ORDER BY score DESC
            LIMIT ${{len(params)+2}}
        """
        
        # Add search query and limit
        search_terms = "|".join(re.findall(r'\w+', q))
        params.extend([search_terms, k])
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        # Format results
        hits = []
        for row in results:
            hits.append({
                "conv_id": row['conv_id'],
                "msg_id": row['msg_id'], 
                "role": row['role'],
                "ts": row['ts'],
                "text": row['snippet'],
                "score": float(row['score'] or 0),
                "highlights": []
            })
        
        return {"results": hits, "total": len(hits)}
    
    finally:
        cur.close()
        conn.close()

# Get conversation timeline
@app.get("/conversation/{conv_id}/timeline")
def get_timeline(conv_id: str):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT conv_id, msg_id, role, ts::text, text, parent_id, meta
            FROM messages 
            WHERE conv_id = %s 
            ORDER BY ts ASC
        """, (conv_id,))
        
        messages = cur.fetchall()
        return {"messages": messages}
    
    finally:
        cur.close()
        conn.close()

# Build context pack with token budgeting
@app.post("/context/pack")
def build_context_pack(request: Dict[str, Any], max_tokens: int = 6000):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        message_ids = request.get('message_ids', [])
        if not message_ids:
            return {"text_block": "", "token_count": 0}
        
        # Fetch messages
        placeholders = ",".join(["%s"] * len(message_ids))
        query = """
            SELECT msg_id, role, ts::text, text
            FROM messages 
            WHERE (conv_id, msg_id) IN (
                SELECT unnest(%s::text[]), unnest(%s::text[])
            )
            ORDER BY ts ASC
        """
        
        conv_ids, msg_ids = zip(*[m.split('/') for m in message_ids])
        cur.execute(query, (list(conv_ids), list(msg_ids)))
        messages = cur.fetchall()
        
        # Build context block
        context_parts = []
        current_tokens = 0
        enc = tiktoken.Encoding('cl100k_base')  # GPT tokenizer
        
        for msg in messages:
            # Format message with timestamp
            formatted = f"[{msg['role']} • {msg['ts'][:16]}] {msg['text']}"
            msg_tokens = len(enc.encode(formatted))
            
            if current_tokens + msg_tokens > max_tokens:
                break
                
            context_parts.append(formatted)
            current_tokens += msg_tokens
        
        text_block = "\n\n".join(context_parts)
        if len(messages) > len(context_parts):
            text_block += f"\n\n-- Truncated at {max_tokens} tokens --"
        
        return {
            "text_block": text_block,
            "token_count": current_tokens,
            "message_count": len(context_parts)
        }
    
    finally:
        cur.close()
        conn.close()