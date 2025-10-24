# api/services/search.py
"""Search-related helper utilities."""

from __future__ import annotations

import re
from typing import List, Sequence

__all__ = ["parse_search_terms", "build_highlights"]


def parse_search_terms(query: str) -> List[str]:
    """Normalise a free-text query into postgres-friendly search terms."""

    if not query:
        return []
    return [term.lower() for term in re.findall(r"\w+", query)]


def build_highlights(text: str, terms: Sequence[str], *, window: int = 40, limit: int = 3) -> List[str]:
    """Construct search highlights for a snippet of text.

    Parameters
    ----------
    text:
        The source text to summarise.
    terms:
        The search terms to highlight.
    window:
        Characters to include on each side of a match.
    limit:
        Maximum number of highlight snippets to return.
    """

    if not text or not terms:
        return []

    normalised_terms = [term.lower() for term in terms if term]
    if not normalised_terms:
        return []

    pattern = re.compile("|".join(re.escape(term) for term in normalised_terms), re.IGNORECASE)

    highlights: List[str] = []
    seen_spans: List[range] = []

    for match in pattern.finditer(text):
        start = max(match.start() - window, 0)
        end = min(match.end() + window, len(text))
        span = range(start, end)

        if any(max(span.start, previous.start) < min(span.stop, previous.stop) for previous in seen_spans):
            continue

        snippet = text[start:end]
        highlighted = snippet.replace(match.group(0), f"**{match.group(0)}**", 1)
        if start > 0:
            highlighted = f"…{highlighted}"
        if end < len(text):
            highlighted = f"{highlighted}…"

        highlights.append(highlighted)
        seen_spans.append(span)

        if len(highlights) >= limit:
            break

    return highlights
