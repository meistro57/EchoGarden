# api/services/normalization.py
"""Utilities for normalising and redacting ingested ChatGPT messages."""

from __future__ import annotations

from datetime import datetime
import hashlib
import re
from typing import Any, Dict, Optional

_DEFAULT_OWNER_ID = "default"


def _safe_text(value: Optional[str]) -> str:
    """Return a consistently typed string for downstream processing."""
    if value is None:
        return ""
    return str(value)


def redact_text(text: Optional[str], enable_pii: bool = True) -> str:
    """Redact common PII markers in a message body.

    Parameters
    ----------
    text:
        The message text to scrub. ``None`` is treated as an empty string.
    enable_pii:
        If ``False`` no redaction is applied – useful for debugging.
    """

    clean_text = _safe_text(text)
    if not enable_pii:
        return clean_text

    # Basic email redaction
    clean_text = re.sub(r"\S+@\S+", "«EMAIL»", clean_text)
    # Phone numbers
    clean_text = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "«PHONE»", clean_text)
    # IPs
    clean_text = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "«IP»", clean_text)
    # URLs
    clean_text = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        "«URL»",
        clean_text,
    )

    return clean_text


def normalize_message(
    msg: Dict[str, Any],
    conv_id: str,
    owner_id: str = _DEFAULT_OWNER_ID,
    *,
    enable_pii: bool = True,
) -> Dict[str, Any]:
    """Normalise a raw message payload for ingestion."""

    text = redact_text(msg.get("content", msg.get("text")), enable_pii=enable_pii)

    canonical_text = _safe_text(msg.get("content", msg.get("text"))).lower().strip()
    hash_value = hashlib.sha256(canonical_text.encode()).hexdigest()

    timestamp = msg.get("create_time", msg.get("timestamp"))
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    normalised = {
        "conv_id": conv_id,
        "msg_id": msg.get("id", hash_value[:8]),
        "owner_id": owner_id,
        "role": msg.get("role", "user"),
        "ts": timestamp,
        "text": text,
        "parent_id": msg.get("parent"),
        "hash": hash_value,
        "meta": {
            "model": msg.get("model"),
            "source": msg.get("source", "chatgpt_export"),
        },
    }
    return normalised


__all__ = ["normalize_message", "redact_text"]
