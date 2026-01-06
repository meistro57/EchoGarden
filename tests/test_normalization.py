# tests/test_normalization.py
"""Unit tests for message normalisation helpers."""

from __future__ import annotations

from datetime import datetime

from api.services.normalization import normalize_message, redact_text


def test_redact_text_removes_common_pii() -> None:
    """PII markers should be redacted when the flag is enabled."""
    sample = "Contact me at bob@example.com or 555-123-4567 from 192.168.0.1 via https://example.com"
    redacted = redact_text(sample)

    assert "bob@example.com" not in redacted
    assert "555-123-4567" not in redacted
    assert "192.168.0.1" not in redacted
    assert "https://example.com" not in redacted
    assert redacted.count("«EMAIL»") == 1
    assert redacted.count("«PHONE»") == 1
    assert redacted.count("«IP»") == 1
    assert redacted.count("«URL»") == 1


def test_redact_text_can_be_disabled() -> None:
    """Redaction should be optional for diagnostic scenarios."""
    sample = "bob@example.com"
    assert redact_text(sample, enable_pii=False) == sample


def test_normalize_message_adds_defaults_and_hash() -> None:
    """Normalisation should enrich and stabilise the payload."""
    raw = {
        "id": "message-1",
        "role": "assistant",
        "content": "Hello Bob",
        "parent": None,
        "model": "gpt-4",
        "source": "chatgpt_export",
    }
    normalised = normalize_message(raw, conv_id="conv-123", owner_id="owner-42")

    assert normalised["conv_id"] == "conv-123"
    assert normalised["msg_id"] == "message-1"
    assert normalised["owner_id"] == "owner-42"
    assert normalised["role"] == "assistant"
    assert normalised["text"] == "Hello Bob"
    assert normalised["meta"] == {"model": "gpt-4", "source": "chatgpt_export"}
    assert len(normalised["hash"]) == 64


def test_normalize_message_generates_timestamp_when_missing() -> None:
    """Messages without timestamps should receive one automatically."""
    raw = {"content": "Hi"}
    normalised = normalize_message(raw, conv_id="conv-xyz")

    timestamp = datetime.fromisoformat(normalised["ts"])
    assert timestamp.year >= 2023  # basic sanity check that ISO parsing succeeds


def test_redact_text_handles_none_input() -> None:
    """None input should be treated as an empty string."""
    result = redact_text(None)
    assert result == ""


def test_normalize_message_handles_missing_content() -> None:
    """Messages with no content should normalize gracefully."""
    raw = {"role": "user"}
    normalised = normalize_message(raw, conv_id="conv-empty")

    assert normalised["text"] == ""
    assert normalised["role"] == "user"
    assert len(normalised["hash"]) == 64


def test_normalize_message_uses_text_field_as_fallback() -> None:
    """When content is missing, text field should be used."""
    raw = {"text": "Hello from text field", "role": "assistant"}
    normalised = normalize_message(raw, conv_id="conv-text")

    assert normalised["text"] == "Hello from text field"
