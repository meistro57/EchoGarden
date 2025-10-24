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
