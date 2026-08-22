"""Document loaders for ingestion (README §23 — "Build document ingestion pipeline").

Yields :class:`RawDoc` records from files or directories, dispatching by extension:

  - ``.jsonl`` — one pre-structured record per line (the seed corpus format):
    ``{"content": "...", "source": "NGSS", "meta": {...}}``.
  - ``.txt`` / ``.md`` — plain text (stdlib only).
  - ``.pdf`` — text extraction via ``pypdf`` (imported lazily).
  - ``.html`` / ``.htm`` — visible text via ``beautifulsoup4`` (imported lazily).

PDF/HTML parsers are optional dependencies imported inside their loader, so the
offline test suite (which never loads those formats) needs neither installed.
Directories are walked recursively; unsupported extensions are skipped and reported
to the caller via :func:`load_documents`'s companion :func:`iter_supported`.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

TEXT_SUFFIXES = {".txt", ".md"}
JSONL_SUFFIXES = {".jsonl"}
PDF_SUFFIXES = {".pdf"}
HTML_SUFFIXES = {".html", ".htm"}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES | JSONL_SUFFIXES | PDF_SUFFIXES | HTML_SUFFIXES


@dataclass
class RawDoc:
    """A source document prior to chunking. ``meta`` is carried onto every chunk."""

    source: str
    text: str
    meta: dict = field(default_factory=dict)


def iter_supported(paths: Iterable[str | Path]) -> Iterator[Path]:
    """Yield supported files under ``paths`` (files or directories), sorted for determinism."""
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            yield from sorted(f for f in p.rglob("*") if f.suffix.lower() in SUPPORTED_SUFFIXES)
        elif p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES:
            yield p


def load_documents(paths: Iterable[str | Path]) -> Iterator[RawDoc]:
    """Load every supported file under ``paths`` into :class:`RawDoc` records."""
    for path in iter_supported(paths):
        yield from _load_file(path)


def _load_file(path: Path) -> Iterator[RawDoc]:
    suffix = path.suffix.lower()
    if suffix in JSONL_SUFFIXES:
        yield from _load_jsonl(path)
    elif suffix in TEXT_SUFFIXES:
        yield RawDoc(
            source=path.stem,
            text=path.read_text(encoding="utf-8"),
            meta={"doc_type": suffix.lstrip("."), "path": str(path)},
        )
    elif suffix in PDF_SUFFIXES:
        yield RawDoc(
            source=path.stem, text=_read_pdf(path), meta={"doc_type": "pdf", "path": str(path)}
        )
    elif suffix in HTML_SUFFIXES:
        yield RawDoc(
            source=path.stem, text=_read_html(path), meta={"doc_type": "html", "path": str(path)}
        )


def _load_jsonl(path: Path) -> Iterator[RawDoc]:
    """Parse a JSONL corpus file; fail loudly with line context on malformed JSON."""
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            content = record.get("content")
            if not content:
                raise ValueError(f"{path}:{lineno}: record missing non-empty 'content'")
            meta = dict(record.get("meta") or {})
            yield RawDoc(source=record.get("source") or path.stem, text=content, meta=meta)


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError("PDF ingestion requires 'pypdf' (add it to the environment)") from exc
    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()


def _read_html(path: Path) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError(
            "HTML ingestion requires 'beautifulsoup4' (add it to the environment)"
        ) from exc
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n").strip()
