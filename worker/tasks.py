"""Worker tasks for embeddings and analytics."""

import logging
import os
from celery import Celery
from openai import OpenAI, OpenAIError
import psycopg2

# Configure logging
logger = logging.getLogger(__name__)

# Celery setup
app = Celery('worker', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

# OpenAI client
openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_db():
    """Get database connection."""
    return psycopg2.connect(dsn=os.getenv("DATABASE_URL"))

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def embed_message(self, conv_id: str, msg_id: str):
    """Compute and store embedding for a message.

    Args:
        conv_id: Conversation identifier
        msg_id: Message identifier

    Returns:
        None
    """
    conn = None
    cur = None

    try:
        conn = get_db()
        cur = conn.cursor()

        # Get message text
        cur.execute("SELECT text, hash FROM messages WHERE conv_id = %s AND msg_id = %s", (conv_id, msg_id))
        row = cur.fetchone()
        if not row:
            logger.warning(f"Message not found: {conv_id}/{msg_id}")
            return

        text, hash_value = row

        # Check if already embedded
        cur.execute("SELECT 1 FROM message_embeddings WHERE conv_id = %s AND msg_id = %s", (conv_id, msg_id))
        if cur.fetchone():
            logger.info(f"Message already embedded: {conv_id}/{msg_id}")
            return

        # Compute embedding
        try:
            response = openai.embeddings.create(
                input=text,
                model="text-embedding-3-large"
            )
            embedding = response.data[0].embedding
        except OpenAIError as e:
            logger.error(f"OpenAI API error for {conv_id}/{msg_id}: {e}")
            # Retry the task
            raise self.retry(exc=e)

        # Store
        cur.execute("""
            INSERT INTO message_embeddings (conv_id, msg_id, embedding, model)
            VALUES (%s, %s, %s, %s)
        """, (conv_id, msg_id, embedding, "text-embedding-3-large"))

        conn.commit()
        logger.info(f"Successfully embedded message: {conv_id}/{msg_id}")

    except psycopg2.Error as e:
        logger.error(f"Database error for {conv_id}/{msg_id}: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        logger.exception(f"Unexpected error embedding message {conv_id}/{msg_id}: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.start()