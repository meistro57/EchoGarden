# api/services/topics.py
"""Topic extraction utilities for analytic surfaces."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import re
from typing import Dict, Iterable, List, MutableMapping, Optional, Sequence

__all__ = ["TopicSample", "TopicBundle", "extract_topics"]

_WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9']+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "he",
    "her",
    "here",
    "him",
    "his",
    "i",
    "in",
    "into",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "she",
    "so",
    "that",
    "the",
    "their",
    "them",
    "there",
    "they",
    "this",
    "to",
    "we",
    "with",
    "you",
    "your",
}


@dataclass(slots=True)
class TopicSample:
    """Represents a message used as an anchor for a topic label."""

    conv_id: str
    msg_id: str
    ts: Optional[str]
    role: Optional[str]
    text: str


@dataclass(slots=True)
class TopicBundle:
    """Aggregated analytics for a derived topic."""

    label: str
    occurrences: int
    weight: float
    first_seen_ts: Optional[str]
    anchors: List[TopicSample]


def _tokenise(text: Optional[str]) -> Iterable[str]:
    """Yield normalised tokens from free-form text."""

    if not text:
        return []

    tokens = {match.group(0).lower() for match in _WORD_PATTERN.finditer(text)}
    return [token for token in tokens if token not in _STOPWORDS and len(token) > 2 and not token.isdigit()]


def _record_sample(
    store: MutableMapping[str, List[TopicSample]],
    token: str,
    message: Dict[str, Optional[str]],
    sample_limit: int,
) -> None:
    """Persist a bounded set of anchor samples for the given token."""

    if token not in store:
        store[token] = []

    sample = TopicSample(
        conv_id=str(message.get("conv_id", "")),
        msg_id=str(message.get("msg_id", "")),
        ts=message.get("ts"),
        role=message.get("role"),
        text=_trim_text(message.get("text")),
    )
    store[token].append(sample)
    store[token].sort(key=lambda item: (item.ts or "", item.msg_id))

    if len(store[token]) > sample_limit:
        del store[token][sample_limit:]


def _trim_text(text: Optional[str], *, limit: int = 280) -> str:
    """Return a bounded preview of message text for analytics payloads."""

    clean_text = (text or "").strip()
    if len(clean_text) <= limit:
        return clean_text
    return f"{clean_text[:limit].rstrip()}…"


def extract_topics(
    messages: Sequence[Dict[str, Optional[str]]],
    *,
    limit: int = 10,
    min_occurrences: int = 2,
    sample_limit: int = 3,
) -> List[TopicBundle]:
    """Derive coarse topics from a collection of messages."""

    if limit < 1:
        raise ValueError("limit must be positive")
    if min_occurrences < 1:
        raise ValueError("min_occurrences must be positive")
    if sample_limit < 1:
        raise ValueError("sample_limit must be positive")

    counter: Counter[str] = Counter()
    first_seen: Dict[str, Optional[str]] = {}
    samples: MutableMapping[str, List[TopicSample]] = defaultdict(list)

    total_messages = len(messages)
    if total_messages == 0:
        return []

    for message in messages:
        unique_tokens = _tokenise(message.get("text"))
        if not unique_tokens:
            continue

        for token in unique_tokens:
            counter[token] += 1
            if token not in first_seen:
                first_seen[token] = message.get("ts")
            _record_sample(samples, token, message, sample_limit)

    filtered_tokens = [
        token for token, count in counter.items() if count >= min_occurrences
    ]

    if not filtered_tokens:
        return []

    filtered_tokens.sort(key=lambda token: (-counter[token], first_seen.get(token) or ""))

    bundles: List[TopicBundle] = []
    for token in filtered_tokens[:limit]:
        occurrences = counter[token]
        weight = occurrences / total_messages
        bundles.append(
            TopicBundle(
                label=token,
                occurrences=occurrences,
                weight=weight,
                first_seen_ts=first_seen.get(token),
                anchors=list(samples[token]),
            )
        )

    return bundles
