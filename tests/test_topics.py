# tests/test_topics.py
"""Unit tests for topic extraction utilities."""

from __future__ import annotations

import pytest

from api.services.topics import extract_topics


def _make_message(conv_id: str, msg_id: str, text: str, ts: str, role: str = "user") -> dict:
    return {
        "conv_id": conv_id,
        "msg_id": msg_id,
        "text": text,
        "ts": ts,
        "role": role,
    }


def test_extract_topics_basic() -> None:
    messages = [
        _make_message("c1", "m1", "Discuss quantum computing and superconducting qubits", "2024-01-01T00:00:00"),
        _make_message("c1", "m2", "Quantum algorithms beat classical ones", "2024-01-01T01:00:00"),
        _make_message("c2", "m3", "Classical control loops for qubits", "2024-01-02T08:00:00", role="assistant"),
        _make_message("c2", "m4", "Lunch plans unrelated", "2024-01-03T09:15:00"),
    ]

    topics = extract_topics(messages, limit=5, min_occurrences=2)

    assert any(bundle.label == "quantum" for bundle in topics)
    assert any(bundle.label == "qubits" for bundle in topics)

    quantum_bundle = next(bundle for bundle in topics if bundle.label == "quantum")
    assert quantum_bundle.occurrences == 2
    assert pytest.approx(quantum_bundle.weight, rel=1e-3) == 0.5
    assert quantum_bundle.anchors[0].msg_id == "m1"


def test_extract_topics_respects_limits() -> None:
    messages = [
        _make_message("c1", "m1", "alpha beta gamma", "2024-01-01T00:00:00"),
        _make_message("c1", "m2", "alpha beta", "2024-01-01T01:00:00"),
        _make_message("c1", "m3", "alpha only", "2024-01-01T02:00:00"),
    ]

    topics = extract_topics(messages, limit=1, min_occurrences=2, sample_limit=1)

    assert len(topics) == 1
    assert topics[0].label == "alpha"
    assert len(topics[0].anchors) == 1


@pytest.mark.parametrize(
    "parameter, value",
    [
        ("limit", 0),
        ("min_occurrences", 0),
        ("sample_limit", 0),
    ],
)
def test_extract_topics_validates_parameters(parameter: str, value: int) -> None:
    kwargs = {
        "limit": 5,
        "min_occurrences": 2,
        "sample_limit": 2,
    }
    kwargs[parameter] = value

    with pytest.raises(ValueError):
        extract_topics([_make_message("c", "m", "alpha beta", "2024-01-01T00:00:00")], **kwargs)


def test_extract_topics_filters_stopwords() -> None:
    messages = [
        _make_message("c", "m1", "the the the alpha", "2024-01-01T00:00:00"),
        _make_message("c", "m2", "alpha appears again", "2024-01-02T00:00:00"),
    ]

    topics = extract_topics(messages, limit=3, min_occurrences=2)

    assert [bundle.label for bundle in topics] == ["alpha"]
