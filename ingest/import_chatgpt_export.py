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
def redact_text(text: str, enable_pii: bool = True) -> str:
    if not enable_pii:
        return text
    
    # Basic email redaction
    text = re.sub(r'\S+@\S+', '«EMAIL»', text)
    # Phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '«PHONE»', text)
    # IPs
    text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '«IP»', text)
    # URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '«URL»', text)
    
    return text

# Normalize message to JSONL format
def normalize_message(msg: Dict, conv_id: str, owner_id: str = "default") -> Dict:
    text = msg.get('content', msg.get('text', ''))
    text = redact_text(text)
    
    # Compute hash for deduplication
    canonical_text = msg.get('content', msg.get('text', '')).lower().strip()
    hash_value = hashlib.sha256(canonical_text.encode()).hexdigest()
    
    normalized = {
        "conv_id": conv_id,
        "msg_id": msg.get('id', str(hash_value)[:8]),
        "role": msg.get('role', 'user'),
        "ts": msg.get('create_time', msg.get('timestamp', datetime.now().isoformat())),
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
                    normalized = normalize_message(msg['message'], conv_id, owner_id)
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