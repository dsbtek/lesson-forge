"""Deterministic, dependency-free text chunker (README §23 — "Chunk curriculum documents").

Splits documents into overlapping, paragraph-aware chunks sized by character budget.
Short documents (e.g. a single standard) return one chunk unchanged. The overlap
carries a little trailing context into the next chunk so a fact split across a
boundary is still retrievable from at least one chunk.

Character budgets (not tokens) keep this pure and offline-testable; embedding models
have generous context relative to these sizes, so approximate sizing is fine.
"""

from __future__ import annotations

import re

DEFAULT_MAX_CHARS = 1200
DEFAULT_OVERLAP = 150

# Split on blank lines (paragraph boundaries), tolerating trailing whitespace.
_PARA_SPLIT = re.compile(r"\n\s*\n")


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def chunk_text(
    text: str,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """Split ``text`` into chunks of at most ~``max_chars`` characters.

    Paragraphs are kept whole when they fit. A paragraph longer than ``max_chars``
    is hard-split into windows with ``overlap`` characters of carry-over. Empty or
    whitespace-only input yields an empty list.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be in [0, max_chars)")

    text = _normalize(text)
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    buf = ""
    for para in (p.strip() for p in _PARA_SPLIT.split(text)):
        if not para:
            continue
        if len(para) > max_chars:
            # Flush the buffer, then hard-split the oversized paragraph.
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.extend(_split_long(para, max_chars=max_chars, overlap=overlap))
            continue
        candidate = f"{buf}\n\n{para}" if buf else para
        if len(candidate) <= max_chars:
            buf = candidate
        else:
            chunks.append(buf)
            buf = para
    if buf:
        chunks.append(buf)
    return chunks


def _split_long(text: str, *, max_chars: int, overlap: int) -> list[str]:
    """Hard-split a single oversized block into overlapping windows."""
    step = max_chars - overlap
    return [text[i : i + max_chars] for i in range(0, len(text), step)]
