# worker/tasks.py
"""Celery tasks responsible for computing embeddings and persisting them."""

from __future__ import annotations

import logging
import os
from typing import Final

from celery import Celery
from openai import OpenAI, OpenAIError
import psycopg2
from psycopg2.extensions import connection as PGConnection

# Configure logging once for the module
LOGGER = logging.getLogger(__name__)

BROKER_URL: Final = os.getenv("REDIS_URL", "redis://localhost:6379/0")
EMBEDDING_MODEL: Final = "text-embedding-3-large"
RETRY_DELAY_SECONDS: Final = 60

# Celery setup
app = Celery("worker", broker=BROKER_URL)


def get_db_connection() -> PGConnection:
    """Create a database connection, raising a clear error if misconfigured."""

    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        msg = "DATABASE_URL environment variable is required for worker tasks."
        raise RuntimeError(msg)

    return psycopg2.connect(dsn=dsn)


def get_openai_client() -> OpenAI:
    """Return a configured OpenAI client, validating environment configuration."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        msg = "OPENAI_API_KEY environment variable is required for embedding tasks."
        raise RuntimeError(msg)

    return OpenAI(api_key=api_key)


@app.task(bind=True, max_retries=3, default_retry_delay=RETRY_DELAY_SECONDS)
def embed_message(self, conv_id: str, msg_id: str) -> None:
    """Compute and persist an embedding for a conversation message."""

    try:
        client = get_openai_client()
    except RuntimeError as exc:  # Environment not configured correctly
        LOGGER.error("Embedding aborted due to configuration error: %s", exc)
        raise

    try:
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT text FROM messages WHERE conv_id = %s AND msg_id = %s",
                (conv_id, msg_id),
            )
            row = cur.fetchone()
            if not row:
                LOGGER.warning("Message not found: %s/%s", conv_id, msg_id)
                return

            (text,) = row

            cur.execute(
                "SELECT 1 FROM message_embeddings WHERE conv_id = %s AND msg_id = %s",
                (conv_id, msg_id),
            )
            if cur.fetchone():
                LOGGER.info("Message already embedded: %s/%s", conv_id, msg_id)
                return

            try:
                response = client.embeddings.create(input=text, model=EMBEDDING_MODEL)
                embedding = response.data[0].embedding
            except OpenAIError as exc:
                LOGGER.error("OpenAI API error for %s/%s: %s", conv_id, msg_id, exc)
                raise self.retry(exc=exc)

            cur.execute(
                """
                INSERT INTO message_embeddings (conv_id, msg_id, embedding, model)
                VALUES (%s, %s, %s, %s)
                """,
                (conv_id, msg_id, embedding, EMBEDDING_MODEL),
            )

            LOGGER.info("Successfully embedded message: %s/%s", conv_id, msg_id)

    except psycopg2.Error as exc:
        LOGGER.error("Database error for %s/%s: %s", conv_id, msg_id, exc)
        raise
    except Exception as exc:  # pragma: no cover - defensive guard
        LOGGER.exception("Unexpected error embedding message %s/%s: %s", conv_id, msg_id, exc)
        raise


if __name__ == "__main__":
    app.start()
