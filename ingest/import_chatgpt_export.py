import json
import zipfile
import click
import psycopg2
from psycopg2.extras import execute_batch
import hashlib
import re
from pathlib import Path
from datetime import datetime
import os

# PII Redaction (configurable)
def redact_text(text: str | dict, enable_pii: bool = True) -> str:
    if not enable_pii:
        if isinstance(text, str):
            return text
        return json.dumps(text)
    
    # Convert dict to string if needed
    text_str = json.dumps(text) if isinstance(text, dict) else text
    
    # Basic email redaction
    text_str = re.sub(r'\S+@\S+', '«EMAIL»', text_str)
    # Phone numbers
    text_str = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '«PHONE»', text_str)
    # IPs
    text_str = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '«IP»', text_str)
    # URLs
    text_str = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '«URL»', text_str)
    
    return text_str

# Normalize message to JSONL format
from typing import Dict, Any
def normalize_message(msg: Dict[str, Any], conv_id: str, owner_id: str = "default", fallback_ts: float = None) -> Dict:
    text = msg.get('content', msg.get('text', ''))
    text = redact_text(text)

    # Compute hash for deduplication
    canonical_text = text.lower().strip()  # Use already redacted text
    hash_value = hashlib.sha256(canonical_text.encode()).hexdigest()

    # Handle timestamp - msg timestamps can be None, so use 'or' for fallback
    ts = msg.get('create_time') or msg.get('timestamp')
    if ts is None:
        # Use conversation timestamp if available, otherwise current time
        ts = fallback_ts if fallback_ts else datetime.now().timestamp()

    # Convert Unix timestamp to ISO format if it's a number
    if isinstance(ts, (int, float)):
        ts = datetime.fromtimestamp(ts).isoformat()

    normalized = {
        "conv_id": conv_id,
        "msg_id": msg.get('id', str(hash_value)[:8]),
        "role": msg.get('role', 'user'),
        "ts": ts,
        "text": text,
        "parent_id": msg.get('parent', None),
        "hash": hash_value,
        "meta": {
            "model": msg.get('model', None),
            "source": msg.get('source', 'chatgpt_export'),
        }
    }
    return normalized

def import_chatgpt_export(zip_path: str, db_url: str, owner_id: str = "default"):
    """Import ChatGPT conversations from zip export."""
    conn = psycopg2.connect(dsn=db_url)
    cur = conn.cursor()
    
    try:
        click.echo(f"Opening {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            with zf.open('conversations.json') as f:
                conversations = json.load(f)
        
        total_imported = 0
        conv_count = 0
        
        for conv_data in conversations:
            conv_id = conv_data['id']
            title = conv_data.get('title', 'Untitled')
            fallback_ts = conv_data.get('create_time') or conv_data.get('update_time')

            # Insert conversation
            cur.execute("""
                INSERT INTO conversations (conv_id, title, owner_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (conv_id) DO NOTHING
            """, (conv_id, title, owner_id))
            conv_count += 1
            click.echo(f"Imported conversation: {title}")

            # Insert messages with upsert
            messages = []
            for msg in conv_data.get('mapping', {}).values():
                if msg.get('message'):
                    normalized = normalize_message(msg['message'], conv_id, owner_id, fallback_ts)
                    messages.append((
                        normalized['conv_id'], normalized['msg_id'], normalized['role'],
                        normalized['ts'], normalized['text'], normalized['hash'],
                        json.dumps(normalized['meta'])
                    ))
            
            if messages:
                execute_batch(cur, """
                    INSERT INTO messages (conv_id, msg_id, role, ts, text, hash, meta)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (conv_id, msg_id) DO NOTHING
                """, messages)
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