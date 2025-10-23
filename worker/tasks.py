"""Worker tasks for embeddings and analytics."""

import os
from celery import Celery
from openai import OpenAI
import psycopg2
import json
import hashlib

# Celery setup
app = Celery('worker', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

# OpenAI client
openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_db():
    return psycopg2.connect(dsn=os.getenv("DATABASE_URL"))

@app.task
def embed_message(conv_id: str, msg_id: str):
    """Compute and store embedding for a message."""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get message text
        cur.execute("SELECT text, hash FROM messages WHERE conv_id = %s AND msg_id = %s", (conv_id, msg_id))
        row = cur.fetchone()
        if not row:
            return
        
        text, hash_value = row
        
        # Check if already embedded
        cur.execute("SELECT 1 FROM message_embeddings WHERE conv_id = %s AND msg_id = %s", (conv_id, msg_id))
        if cur.fetchone():
            return
        
        # Compute embedding
        response = openai.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
        embedding = response.data[0].embedding
        
        # Store
        cur.execute("""
            INSERT INTO message_embeddings (conv_id, msg_id, embedding, model)
            VALUES (%s, %s, %s, %s)
        """, (conv_id, msg_id, embedding, "text-embedding-3-large"))
        
        conn.commit()
        
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.start()