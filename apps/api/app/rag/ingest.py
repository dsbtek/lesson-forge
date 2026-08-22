"""Ingestion CLI (README §23 — "Build document ingestion pipeline").

    python -m app.rag.ingest                     # seed corpus only
    python -m app.rag.ingest --paths /knowledge  # seed + a documents directory
    python -m app.rag.ingest --no-seed --paths ./docs

Pipeline: load → chunk → (embed if enabled) → upsert into ``knowledge_chunks``.
Idempotent: each chunk stores a content ``hash`` in ``meta``; re-running skips chunks
already present, so ingestion can be repeated safely. Embeddings are produced only
when :func:`app.rag.embeddings.enabled` is true; otherwise chunks are stored without a
vector and remain retrievable via sparse (FTS) search.

Unlike retrieval (which soft-degrades), ingestion fails loudly on an embedding error —
the operator ran it deliberately and should see the failure.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.knowledge import KnowledgeChunk
from app.rag import chunking, embeddings, loaders

logger = logging.getLogger("app.rag.ingest")

SEED_DIR = Path(__file__).parent / "seed"


def _hash(source: str, content: str) -> str:
    return hashlib.sha256(f"{source}\0{content}".encode()).hexdigest()


def _records(
    docs: Iterable[loaders.RawDoc], *, max_chars: int, overlap: int
) -> list[tuple[str, str, dict[str, Any]]]:
    """Expand documents into (source, chunk, meta) records with content hashes."""
    out: list[tuple[str, str, dict[str, Any]]] = []
    for doc in docs:
        chunks = chunking.chunk_text(doc.text, max_chars=max_chars, overlap=overlap)
        for i, chunk in enumerate(chunks):
            meta = {**doc.meta, "hash": _hash(doc.source, chunk), "chunk_index": i}
            out.append((doc.source, chunk, meta))
    return out


def _batches(items: list[Any], size: int) -> Iterator[list[Any]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


async def _existing_hashes(db, hashes: list[str]) -> set[str]:
    if not hashes:
        return set()
    rows = await db.execute(
        select(KnowledgeChunk.meta["hash"].astext).where(
            KnowledgeChunk.meta["hash"].astext.in_(hashes)
        )
    )
    return {h for h in rows.scalars().all() if h}


async def ingest(
    paths: Iterable[str],
    *,
    include_seed: bool = True,
    batch_size: int = 64,
    max_chars: int = chunking.DEFAULT_MAX_CHARS,
    overlap: int = chunking.DEFAULT_OVERLAP,
) -> dict[str, int]:
    """Load, chunk, embed, and upsert documents. Returns a summary count dict."""
    sources = list(paths)
    if include_seed:
        sources.append(str(SEED_DIR))

    docs = list(loaders.load_documents(sources))
    records = _records(docs, max_chars=max_chars, overlap=overlap)
    logger.info("loaded %d document(s) → %d chunk(s)", len(docs), len(records))

    embed_on = embeddings.enabled()
    inserted = skipped = 0
    async with async_session_factory() as db:
        for batch in _batches(records, batch_size):
            existing = await _existing_hashes(db, [m["hash"] for _, _, m in batch])
            seen: set[str] = set()
            fresh = []
            for src, content, meta in batch:
                h = meta["hash"]
                if h in existing or h in seen:
                    skipped += 1
                    continue
                seen.add(h)
                fresh.append((src, content, meta))
            if not fresh:
                continue

            vectors = embeddings.embed_texts([c for _, c, _ in fresh]) if embed_on else None
            for j, (src, content, meta) in enumerate(fresh):
                db.add(
                    KnowledgeChunk(
                        source=src,
                        content=content,
                        meta=meta,
                        embedding=vectors[j] if vectors else None,
                    )
                )
                inserted += 1
            await db.commit()

    summary = {
        "documents": len(docs),
        "chunks": len(records),
        "inserted": inserted,
        "skipped": skipped,
        "embedded": inserted if embed_on else 0,
    }
    logger.info("ingest complete: %s", summary)
    return summary


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest curriculum documents into knowledge_chunks.")
    p.add_argument("--paths", nargs="*", default=[], help="Files or directories to ingest.")
    p.add_argument("--no-seed", action="store_true", help="Skip the bundled seed corpus.")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--max-chars", type=int, default=chunking.DEFAULT_MAX_CHARS)
    p.add_argument("--overlap", type=int, default=chunking.DEFAULT_OVERLAP)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _parse_args(argv)
    summary = asyncio.run(
        ingest(
            args.paths,
            include_seed=not args.no_seed,
            batch_size=args.batch_size,
            max_chars=args.max_chars,
            overlap=args.overlap,
        )
    )
    print(
        f"Ingested {summary['inserted']} chunk(s) "
        f"({summary['skipped']} already present, {summary['embedded']} embedded) "
        f"from {summary['documents']} document(s)."
    )


if __name__ == "__main__":
    main()
