"""The text chunker is pure, deterministic, and respects its size budget
(app/rag/chunking.py)."""

from __future__ import annotations

import pytest

from app.rag.chunking import chunk_text


def test_empty_or_whitespace_yields_nothing():
    assert chunk_text("") == []
    assert chunk_text("   \n\n\t ") == []


def test_short_text_is_one_stripped_chunk():
    assert chunk_text("  a single standard.  ") == ["a single standard."]


def test_crlf_is_normalized():
    assert chunk_text("line one\r\nline two") == ["line one\nline two"]


def test_small_paragraphs_pack_into_one_chunk():
    text = "A" * 10 + "\n\n" + "B" * 10
    assert chunk_text(text, max_chars=40, overlap=5) == ["A" * 10 + "\n\n" + "B" * 10]


def test_paragraphs_split_when_they_would_exceed_budget():
    text = "A" * 30 + "\n\n" + "B" * 30  # combined 62 > 40, each fits
    chunks = chunk_text(text, max_chars=40, overlap=5)
    assert chunks == ["A" * 30, "B" * 30]


def test_oversized_paragraph_is_hard_split_with_overlap():
    text = "a" * 100  # one paragraph, no blank lines
    chunks = chunk_text(text, max_chars=40, overlap=10)
    # step = 30 → windows at 0, 30, 60, 90.
    assert [len(c) for c in chunks] == [40, 40, 40, 10]
    # Consecutive chunks share `overlap` characters of context.
    assert chunks[0][-10:] == chunks[1][:10]


def test_every_chunk_respects_max_chars():
    text = ("Sentence about ecosystems. " * 200).strip()
    chunks = chunk_text(text, max_chars=200, overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)


def test_deterministic():
    text = ("Water cycle. " * 300).strip()
    assert chunk_text(text, max_chars=150, overlap=30) == chunk_text(
        text, max_chars=150, overlap=30
    )


@pytest.mark.parametrize(
    "max_chars, overlap",
    [(0, 0), (-1, 0), (100, -1), (100, 100), (100, 150)],
)
def test_invalid_parameters_raise(max_chars, overlap):
    with pytest.raises(ValueError):
        chunk_text("some text", max_chars=max_chars, overlap=overlap)
