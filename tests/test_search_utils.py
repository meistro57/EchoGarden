# tests/test_search_utils.py
"""Tests for search utility helpers."""

from __future__ import annotations

from api.services.search import build_highlights, parse_search_terms


def test_parse_search_terms_normalises_words() -> None:
    """Queries should be split into lowercase search tokens."""

    query = "Hello, World!"
    assert parse_search_terms(query) == ["hello", "world"]


def test_build_highlights_returns_snippets() -> None:
    """Highlight builder should emphasise matched segments."""

    snippet = "The quick brown fox jumps over the lazy dog"
    highlights = build_highlights(snippet, ["Quick", "dog"], window=5)

    assert len(highlights) == 2
    assert "**quick**" in highlights[0].lower()
    assert highlights[-1].endswith("**dog**") or "**dog**" in highlights[-1]


def test_build_highlights_avoids_duplicate_overlaps() -> None:
    """Overlapping matches should be collapsed into a single snippet."""

    snippet = "alpha beta alpha beta"
    highlights = build_highlights(snippet, ["alpha"], window=10)

    assert len(highlights) == 1
    assert highlights[0].count("**alpha**") == 1


def test_parse_search_terms_handles_empty_query() -> None:
    """Empty query should return an empty list."""
    assert parse_search_terms("") == []
    assert parse_search_terms("   ") == []


def test_build_highlights_handles_empty_inputs() -> None:
    """Empty text or terms should return an empty list."""
    assert build_highlights("", ["term"]) == []
    assert build_highlights("some text", []) == []
    assert build_highlights("some text", [""]) == []


def test_build_highlights_respects_limit() -> None:
    """Highlights should stop at the configured limit."""
    snippet = "alpha beta gamma delta alpha beta gamma delta alpha beta gamma delta"
    highlights = build_highlights(snippet, ["alpha", "beta", "gamma", "delta"], window=3, limit=2)
    assert len(highlights) == 2
