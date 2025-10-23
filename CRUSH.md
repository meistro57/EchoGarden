MCP Chat Log Intelligence System — Comprehensive Build Plan
A single drop-in plan you can paste into a coding model (or hand to a team) to implement an MCP-enabled system that ingests ChatGPT exports, normalizes to JSONL, indexes + vectors them, exposes useful search/context tools, and ships with a lean web UI.

0) TL;DR (Goals & Non‑Goals)
Goals

Ingest ChatGPT exports (conversations.json, loose .md/.txt) and normalize to one-message-per-line JSONL.
Store messages durably (Postgres) and semantically (pgvector/Qdrant), with raw artifacts in object storage (MinIO).
Provide MCP tools for: hybrid search, timelines, context-pack assembly, topic map.
Ship an API (FastAPI) and UI (Next.js + shadcn/ui) with a “Context Builder” (token‑budget aware).
Privacy: PII redaction, owner‑scoped access, checksums for integrity.
Deploy via Docker Compose with observability.
Non‑Goals (for v1)

Live sync from third‑party chat systems (can be v2 via connectors).
Agentic auto‑summarization of entire history (ship later as batch jobs).
1) Repo Layout
chat-bridge-logs/
├─ api/                 # FastAPI app (REST + MCP server)
├─ worker/              # Celery/Arq jobs: embeddings, NER, topics
├─ ui/                  # Next.js (app router) + shadcn/ui
├─ ingest/              # Importers + normalizers + CLI
├─ infra/               # docker-compose, migrations, grafana, prom
├─ schemas/             # OpenAPI, JSON Schemas, MCP manifests
├─ scripts/             # Dev scripts / utilities
└─ README.md
2) Data Model (Logical)
2.1 Message JSONL (normalized)
Each line is one atomic message.

{"conv_id":"c_20251010_161638","msg_id":"2","parent_id":"1","role":"assistant","ts":"2025-10-10T16:16:50Z","text":"Absolutely! Designing ...","meta":{"model":"gpt-4o-mini","persona":"ADHD_Kid","source":"chatgpt_export"}}
Required fields: conv_id, msg_id, role, ts, text
Optional: parent_id, meta.model, meta.persona, meta.source, attachments[] (paths/urls, mime), hash (sha256 of canonicalized text)

2.2 PostgreSQL (DDL sketch)
-- conversations
CREATE TABLE conversations (
  conv_id       TEXT PRIMARY KEY,
  title         TEXT,
  owner_id      TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  checksum      TEXT,                 -- rolling checksum over messages
  meta          JSONB
);

-- messages
CREATE TABLE messages (
  conv_id       TEXT REFERENCES conversations(conv_id) ON DELETE CASCADE,
  msg_id        TEXT,
  role          TEXT CHECK (role IN ('user','assistant','system','tool')),
  ts            TIMESTAMPTZ NOT NULL,
  text          TEXT NOT NULL,
  parent_id     TEXT,
  hash          TEXT,                 -- sha256(text canonical)
  meta          JSONB,
  PRIMARY KEY (conv_id, msg_id)
);
CREATE INDEX idx_messages_ts        ON messages(ts);
CREATE INDEX idx_messages_text_gin  ON messages USING GIN (to_tsvector('english', text));

-- tags (freeform labels)
CREATE TABLE message_tags (
  conv_id   TEXT,
  msg_id    TEXT,
  tag       TEXT,
  PRIMARY KEY (conv_id, msg_id, tag),
  FOREIGN KEY (conv_id, msg_id) REFERENCES messages(conv_id, msg_id) ON DELETE CASCADE
);

-- embeddings (pgvector or external ANN)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE message_embeddings (
  conv_id   TEXT,
  msg_id    TEXT,
  embedding VECTOR(1536),
  model     TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (conv_id, msg_id),
  FOREIGN KEY (conv_id, msg_id) REFERENCES messages(conv_id, msg_id) ON DELETE CASCADE
);

-- entities/sentiment/topics
CREATE TABLE message_analytics (
  conv_id   TEXT,
  msg_id    TEXT,
  sentiment NUMERIC,
  entities  JSONB,
  topics    TEXT[],
  PRIMARY KEY (conv_id, msg_id),
  FOREIGN KEY (conv_id, msg_id) REFERENCES messages(conv_id, msg_id) ON DELETE CASCADE
);
3) Ingestion & Normalization
3.1 Importers
import_chatgpt_export.py → unzip, parse conversations.json → emit *.jsonl per conversation.
import_markdown.py → parse role/ts heuristics from .md/.txt if present, else assign synthetic timestamps (file mtime + order).
import_folder.py → recurse directory; route files by extension.
3.2 Normalization Rules
Canonicalize line endings, trim trailing spaces.
Strip code fences to raw text for embeddings (retain in meta.formatting for UI rendering).
Compute hash = sha256(lowercase(trim(text))) to dedupe.
Maintain idempotency: re-importing same export should not duplicate rows (use hash + (conv_id,msg_id) upsert).
3.3 PII Redaction (configurable)
Regex pass (EMAIL, PHONE, IP, URL).
NER pass (names/locations) → replace with «NAME» etc. Store reversible map per owner if needed.
4) Processing Pipeline (Worker)
Queue: Celery (Redis) or Arq (Redis).
Jobs

embed_message → compute vector; skip if hash unchanged.
analyze_message → sentiment (−1..+1), entities (spans + types), topics (BERTopic or light LDA on rolling window).
update_checksum → recompute conversation manifest after batch.
Retry on transient errors; backoff jitter. Metrics per stage.

5) Search & Ranking
Hybrid = BM25/tsvector + ANN re‑rank.

Primary candidates: SELECT ... ORDER BY ts_rank_cd(...) DESC LIMIT 200.
Re‑rank top N with cosine similarity to query embedding.
Optional MMR (diversity) for top‑k display.
Filters: conv_id, date range, role, persona, tags, model.

Highlights: store token offsets for UI bolding.

6) API (FastAPI) — Contract
6.1 Endpoints
GET  /health
POST /ingest/chatgpt-export    (multipart: zip) → { imported: n, conversations: m }
POST /ingest/jsonl             (multipart: file) → { imported: n }
GET  /search?q=...&k=50&filters=... → [{hit}]
GET  /conversation/{conv_id}/timeline → [{message}]
POST /context/pack             { "message_ids": [...] , "max_tokens": 6000 } → { text_block, token_count }
GET  /topics?from=...&to=... → { topics: [{label, weight, anchors: [msg_id]}] }
Hit shape

{
  "conv_id": "c_...",
  "msg_id": "42",
  "role": "assistant",
  "ts": "2025-10-10T16:16:50Z",
  "text": "...snippet with highlights...",
  "score": 0.87,
  "highlights": [{"start":123,"end":137}]
}
6.2 Auth
Bearer tokens (owner-scoped).
Optional API keys per service.
7) MCP Tools (Manifest + Semantics)
7.1 Manifest (schemas/mcp.manifest.json)
{
  "name": "chat-log-mcp",
  "version": "0.1.0",
  "tools": [
    {
      "name": "search_messages",
      "description": "Hybrid search over chat logs with filters.",
      "input_schema": {"type":"object","properties":{"query":{"type":"string"},"k":{"type":"integer"},"filters":{"type":"object"}}}
    },
    {
      "name": "get_timeline",
      "description": "Return ordered messages for a conversation.",
      "input_schema": {"type":"object","properties":{"conv_id":{"type":"string"}}}
    },
    {
      "name": "build_context_pack",
      "description": "Create prompt-ready block from message IDs with token budgeting.",
      "input_schema": {"type":"object","properties":{"message_ids":{"type":"array","items":{"type":"string"}},"max_tokens":{"type":"integer"}}}
    },
    {
      "name": "topic_map",
      "description": "Return topic labels and anchor messages over a time range.",
      "input_schema": {"type":"object","properties":{"from":{"type":"string"},"to":{"type":"string"}}}
    }
  ]
}
7.2 Tool Semantics
search_messages: returns ranked hits with message_ids for chaining.
get_timeline: includes lightweight prev/next pointers for UI paging.
build_context_pack: concatenates messages with role headers, ensures token limit with graceful truncation (front‑load and tail‑keep), returns both text_block and segments[] metadata.
topic_map: outputs {label, weight, anchors[]} for UI cloud + drilldown.
8) UI (Next.js + shadcn/ui)
Pages

/ Global search (query box, filters, results list)
/c/[conv_id] Timeline view (sticky date markers, role chips, persona/model badges)
/context Context Builder (left: search; middle: selected items; right: live token counter + export)
Components

MessageCard: role chip, timestamp, copy actions, “Add to Context”
TokenGauge: shows % of target model budget (configurable per model)
TopicCloud: topic chips → click to filter
Quality of life

Keyboard nav (/ focus search, a add to pack)
Dark mode default
9) Deployment (Docker Compose)
Services: api, worker, db (Postgres + pgvector), redis, minio, ui, qdrant (optional), prometheus, grafana.

infra/docker-compose.yml (excerpt)

services:
  db:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]
  redis:
    image: redis:7
    ports: ["6379:6379"]
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio123
    ports: ["9000:9000","9001:9001"]
  api:
    build: ../api
    env_file: ../infra/.env
    depends_on: [db, redis, minio]
    ports: ["8000:8000"]
  worker:
    build: ../worker
    env_file: ../infra/.env
    depends_on: [db, redis]
  ui:
    build: ../ui
    environment:
      NEXT_PUBLIC_API_BASE: http://localhost:8000
    ports: ["3000:3000"]
Envs (infra/.env.example)

DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
REDIS_URL=redis://redis:6379/0
OBJECT_STORE_ENDPOINT=http://minio:9000
OBJECT_STORE_BUCKET=chat-logs
OBJECT_STORE_ACCESS_KEY=minio
OBJECT_STORE_SECRET_KEY=minio123
EMBED_MODEL=openai/text-embedding-3-large
OPENAI_API_KEY=changeme
PII_REDACTION=true
10) Security & Privacy
Auth: owner‑scoped tokens; all queries require owner_id context.
Row‑level security: scope by owner_id (Postgres RLS) or enforce in service.
Encryption: TLS on public endpoints; at‑rest via volume encryption if required.
PII: configurable redaction; reversible map is encrypted per owner.
Integrity: per‑conversation manifest (Merkle of message hashes).
11) Observability
Prometheus counters: ingest_messages_total, embed_calls_total, embed_cache_hits_total, search_queries_total.
Traces: OpenTelemetry for ingest → DB → embed → index.
Dashboards: time to index, queue depth, error rate, 95p search latency.
12) Testing Strategy
Unit: importers (golden exports), normalizer idempotency, redaction patterns.
Integration: search ranking parity (snapshots), context pack token budgeting, RLS tests.
E2E: ingest zip → search → add to context → export block.
13) Developer UX
make dev-up → docker compose up + seed sample export.
scripts/dev_seed.sh → download small anonymized sample → run import → run embeddings with mock model if no key.
Hot‑reload in api/ and ui/ using bind mounts.
14) Roadmap (Milestones)
M1 (Core ingest)

JSONL normalizer, Postgres tables, basic import CLI, idempotent upsert.
M2 (Search + vectors)

Embedding worker, pgvector ANN, hybrid search endpoint, UI global search.
M3 (Context Builder + MCP)

Context pack endpoint (token‑aware), MCP manifest + tools, UI context workspace.
M4 (Topics + analytics)

Topic map job + UI, keeper rate, persona/model mix stats.
M5 (Privacy + integrity)

PII redaction toggles, RLS/ACL, checksum manifests, audit log.
M6 (Polish + deploy)

Grafana dashboards, seeds, docs, production profile.
15) Acceptance Criteria (v1)
Importing a standard ChatGPT export produces N JSONL lines matching message count (± system/tool) with zero duplicates on re‑import.
Search returns relevant results within 200 ms p95 on 100k messages (local dev hardware), and 800 ms p95 on 1M messages (ANN enabled).
Context Builder reliably holds 6k tokens of mixed messages and exports a copy‑paste block with role headers.
MCP tools callable from ChatBridge returning correct structures.
16) Example: Context Pack Format
[system] You are assembling high-signal excerpts from prior chats.
[user • 2025-10-10 16:16] …
[assistant • 2025-10-10 16:17] …
…
---
Tokens: 5,842 / 8,192 (model: gpt-4o)
Provenance: conv_id=c_20251010_161638; ids=[7,9,12,14]
17) Notes for Windows/WSL & Pop!_OS
Prefer Docker Desktop (Windows) with WSL2 backend; bind‑mount repo to Linux path.
Use python / pip alias assumptions in scripts.
File watching: enable polling in Next.js if needed under WSL2.
18) Risk Register (early)
Embedding cost/latency → add on‑disk cache keyed by hash+model.
Schema drift of exports → keep importers tolerant, log anomalies.
Personally sensitive logs → default PII redaction ON; gated override.
19) Nice‑to‑Have (Post‑v1)
On‑demand abstractive summaries per conversation.
Cross‑conversation thread stitcher (detect continuations).
RAG over code blocks only (developer mode).
Pluggable local embeddings (text-embeddings-instructor, bge-large).
20) Definition of Done
docker compose up starts full stack.
scripts/dev_seed.sh ingests sample data without secrets.
Open http://localhost:3000 → search → select → export context.
MCP tools pass contract tests.
END
