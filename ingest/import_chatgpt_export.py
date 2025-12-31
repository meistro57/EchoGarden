# import_chatgpt_export.py
import json
import zipfile
import click
import psycopg2
from psycopg2.extras import execute_batch
import hashlib
import re
from pathlib import Path
from datetime import datetime, timezone
import os
from typing import Dict, Any

# ---------------- Schema bootstrap ----------------
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS conversations (
  conv_id   text PRIMARY KEY,
  title     text,
  owner_id  text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
  conv_id  text NOT NULL REFERENCES conversations(conv_id) ON DELETE CASCADE,
  msg_id   text NOT NULL,
  role     text,
  ts       timestamptz,
  text     text,
  hash     text,
  meta     jsonb,
  PRIMARY KEY (conv_id, msg_id)
);

CREATE INDEX IF NOT EXISTS idx_messages_conv_ts  ON messages (conv_id, ts);
CREATE INDEX IF NOT EXISTS idx_messages_hash     ON messages (hash);
CREATE INDEX IF NOT EXISTS idx_conversations_owner ON conversations (owner_id);
"""

def ensure_schema(conn):
    with conn.cursor() as c:
        c.execute(SCHEMA_SQL)
    conn.commit()

# ---------------- PII Redaction ----------------
def redact_text(text: str | dict, enable_pii: bool = True) -> str:
    if not enable_pii:
        if isinstance(text, str):
            return text
        return json.dumps(text)
    text_str = json.dumps(text) if isinstance(text, dict) else text
    text_str = re.sub(r'\S+@\S+', '«EMAIL»', text_str)                       # emails
    text_str = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '«PHONE»', text_str) # phones
    text_str = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '«IP»', text_str) # IPv4
    text_str = re.sub(r'http[s]?://(?:[a-zA-Z0-9$-_.+!*\'(),]|%[0-9a-fA-F]{2})+', '«URL»', text_str) # URLs
    return text_str

def normalize_message(msg: Dict[str, Any], conv_id: str, owner_id: str = "default", fallback_ts: float = None) -> Dict:
    # ChatGPT exports vary; try content->parts first, then content/text fields.
    text = ""
    if isinstance(msg.get("content"), dict) and isinstance(msg["content"].get("parts"), list):
        text = "\n".join([p for p in msg["content"]["parts"] if isinstance(p, str)])
    else:
        text = msg.get("content", msg.get("text", "")) or ""

    text = redact_text(text)

    canonical_text = text.lower().strip()
    hash_value = hashlib.sha256(canonical_text.encode()).hexdigest()

    ts = msg.get('create_time') or msg.get('timestamp') or fallback_ts or datetime.now(timezone.utc).timestamp()
    if isinstance(ts, (int, float)):
        ts = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    role = msg.get('role') or (msg.get('author', {}) or {}).get('role') or 'user'

    normalized = {
        "conv_id": conv_id,
        "msg_id": msg.get('id', hash_value[:8]),
        "role": role,
        "ts": ts,
        "text": text,
        "parent_id": msg.get('parent', None),
        "hash": hash_value,
        "meta": {
            "model": msg.get('model'),
            "source": msg.get('source', 'chatgpt_export'),
        }
    }
    return normalized

def import_chatgpt_export(zip_path: str, db_url: str, owner_id: str = "default"):
    """Import ChatGPT conversations from zip export."""
    conn = psycopg2.connect(dsn=db_url)
    cur = conn.cursor()
    try:
        ensure_schema(conn)  # <<— make sure tables exist

        click.echo(f"Opening {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # ChatGPT export uses conversations.json at the root
            with zf.open('conversations.json') as f:
                conversations = json.load(f)

        total_imported = 0
        conv_count = 0

        for conv_data in conversations:
            conv_id = conv_data['id']
            title = conv_data.get('title', 'Untitled')
            fallback_ts = conv_data.get('create_time') or conv_data.get('update_time')

            # Insert conversation (idempotent)
            cur.execute(
                """
                INSERT INTO conversations (conv_id, title, owner_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (conv_id) DO NOTHING
                """,
                (conv_id, title, owner_id),
            )
            conv_count += 1
            click.echo(f"Imported conversation: {title}")

            messages = []
            # Newer exports put messages under mapping; each node may or may not have a 'message'
            mapping = conv_data.get('mapping', {}) or {}
            for node in mapping.values():
                m = node.get('message')
                if not m:
                    continue
                normalized = normalize_message(m, conv_id, owner_id, fallback_ts)
                messages.append((
                    normalized['conv_id'], normalized['msg_id'], normalized['role'],
                    normalized['ts'], normalized['text'], normalized.get('parent_id'),
                    normalized['hash'], json.dumps(normalized['meta'])
                ))

            if messages:
                execute_batch(
                    cur,
                    """
                    INSERT INTO messages (conv_id, msg_id, role, ts, text, parent_id, hash, meta)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (conv_id, msg_id) DO NOTHING
                    """,
                    messages,
                )
                total_imported += len(messages)

        conn.commit()
        click.echo(f"✅ Imported {total_imported} messages from {conv_count} conversations")
        return total_imported, conv_count

    except Exception as e:
        conn.rollback()
        click.echo(f"❌ Import failed: {e}", err=True)
        raise
    finally:
        cur.close()
        conn.close()

@click.command()
@click.argument('zip_path', type=click.Path(exists=True))
@click.option('--db-url', default='postgresql://postgres:postgres@localhost:5432/postgres')
@click.option('--owner-id', default='default')
def cli(zip_path, db_url, owner_id):
    """Import ChatGPT export from ZIP file."""
    import_chatgpt_export(zip_path, db_url, owner_id)

if __name__ == '__main__':
    cli()
