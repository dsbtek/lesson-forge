"""Hybrid retriever (README §10) — dense ⊕ sparse ⊕ RRF, with authority filtering.

Combines three signals over ``knowledge_chunks`` and fuses them with reciprocal
rank fusion (:mod:`app.rag.fusion`):

  1. **Dense** — pgvector cosine distance on the embedding column (semantic).
  2. **Sparse** — PostgreSQL FTS (``websearch_to_tsquery`` + ``ts_rank_cd``) over the
     generated ``content_tsv`` (keyword / exact-identifier recall).
  3. **Code match** — explicit lookup for requested standard identifiers so exact
     codes (e.g. ``5-ESS2-1``) are never missed.

Results are metadata-filtered (grade/subject), boosted for official sources, and
returned as :class:`RetrievedChunk`. The whole thing is gated by :func:`available`
(``settings.rag_enabled``). :func:`retrieve_for_request` **soft-degrades**: if the
embedding model is unreachable it falls back to sparse-only; if the store itself is
unreachable it returns an empty, ``degraded`` report so generation still completes.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from sqlalchemy import Select, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.knowledge import KnowledgeChunk
from app.rag import embeddings
from app.rag.fusion import fuse_ranked

logger = logging.getLogger(__name__)

# Weights per signal (code matches dominate; dense and sparse balanced).
_WEIGHTS = {"dense": 1.0, "sparse": 1.0, "code": 2.0}
# Additive fused-score bonus for authoritative ("official") sources.
_AUTHORITY_BONUS = 0.01


@dataclass
class RetrievedChunk:
    """One retrieved evidence chunk with its fused score and source metadata."""

    id: str
    source: str | None
    content: str
    meta: dict[str, Any]
    score: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalReport:
    """Outcome of a retrieval call — evidence plus observability for the event stream."""

    evidence: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "none"  # "hybrid" | "sparse" | "none"
    degraded: bool = False
    error: str | None = None

    @property
    def count(self) -> int:
        return len(self.evidence)


def available() -> bool:
    """True when the worker should attempt retrieval (else the researcher falls back)."""
    return bool(settings.rag_enabled)


def _apply_filters(stmt: Select, filters: dict[str, Any] | None) -> Select:
    """Constrain a query by JSONB ``meta`` fields (skips empty values)."""
    if not filters:
        return stmt
    for key in ("grade", "subject", "framework"):
        val = filters.get(key)
        if val:
            stmt = stmt.where(KnowledgeChunk.meta[key].astext == str(val))
    return stmt


async def _ids(db: AsyncSession, stmt: Select) -> list[KnowledgeChunk]:
    return list((await db.execute(stmt)).scalars().all())


async def _gather(
    db: AsyncSession,
    query: str,
    qvec: list[float] | None,
    standards: list[str],
    filters: dict[str, Any] | None,
    candidate_k: int,
) -> tuple[dict[str, KnowledgeChunk], list[list[str]], list[float]]:
    """Run the three retrievers and return (chunks-by-id, ranked-id-lists, weights)."""
    by_id: dict[str, KnowledgeChunk] = {}
    ranked: list[list[str]] = []
    weights: list[float] = []

    def register(rows: list[KnowledgeChunk], weight: float) -> None:
        ids = []
        for c in rows:
            cid = str(c.id)
            by_id.setdefault(cid, c)
            ids.append(cid)
        if ids:
            ranked.append(ids)
            weights.append(weight)

    # 1. Dense (only when a query vector was produced).
    if qvec is not None:
        dense = _apply_filters(
            select(KnowledgeChunk).where(KnowledgeChunk.embedding.is_not(None)), filters
        ).order_by(KnowledgeChunk.embedding.cosine_distance(qvec)).limit(candidate_k)
        register(await _ids(db, dense), _WEIGHTS["dense"])

    # 2. Sparse FTS.
    tsq = func.websearch_to_tsquery("english", query)
    sparse = _apply_filters(
        select(KnowledgeChunk).where(KnowledgeChunk.content_tsv.op("@@")(tsq)), filters
    ).order_by(desc(func.ts_rank_cd(KnowledgeChunk.content_tsv, tsq))).limit(candidate_k)
    register(await _ids(db, sparse), _WEIGHTS["sparse"])

    # 3. Exact standard-code / identifier match (not metadata-filtered — codes are exact).
    if standards:
        conds = []
        for s in standards:
            conds.append(KnowledgeChunk.content.contains(s, autoescape=True))
            conds.append(KnowledgeChunk.meta["code"].astext == s)
        code = select(KnowledgeChunk).where(or_(*conds)).limit(candidate_k)
        register(await _ids(db, code), _WEIGHTS["code"])

    return by_id, ranked, weights


async def _search(
    db: AsyncSession,
    query: str,
    *,
    standards: list[str],
    filters: dict[str, Any] | None,
    limit: int,
) -> tuple[list[RetrievedChunk], str, str | None]:
    """Return (chunks, mode, embed_error). Raises only on store-level failures."""
    embed_error: str | None = None
    qvec: list[float] | None = None
    if embeddings.enabled():
        try:
            qvec = embeddings.embed_query(query)
        except embeddings.EmbeddingError as exc:  # dense unavailable → sparse-only
            embed_error = str(exc)
            logger.warning("RAG dense retrieval degraded to sparse-only: %s", exc)

    candidate_k = max(limit * 4, 20)
    by_id, ranked, weights = await _gather(db, query, qvec, standards, filters, candidate_k)

    # Fallback: if metadata filters starved the result set, retry unfiltered.
    if not by_id and filters:
        by_id, ranked, weights = await _gather(db, query, qvec, standards, None, candidate_k)

    boosts = {
        cid: _AUTHORITY_BONUS
        for cid, c in by_id.items()
        if (c.meta or {}).get("authority_level") == "official"
    }
    fused = fuse_ranked(ranked, weights=weights, boosts=boosts)

    chunks = [
        RetrievedChunk(
            id=cid,
            source=by_id[cid].source,
            content=by_id[cid].content,
            meta=by_id[cid].meta or {},
            score=round(score, 6),
        )
        for cid, score in fused[:limit]
        if cid in by_id
    ]
    mode = "hybrid" if qvec is not None else "sparse"
    return chunks, mode, embed_error


def _build_query(request: dict[str, Any]) -> tuple[str, list[str], dict[str, Any]]:
    parts = [request.get("subject"), request.get("topic"), request.get("grade")]
    standards = [str(s) for s in (request.get("standards") or []) if s]
    query = " ".join(str(p) for p in parts if p)
    query = (query + " " + " ".join(standards)).strip()
    subject = (request.get("subject") or "").strip().lower() or None
    filters = {"grade": request.get("grade") or None, "subject": subject}
    return query, standards, filters


async def retrieve_for_request(
    db: AsyncSession, request: dict[str, Any], *, limit: int | None = None
) -> RetrievalReport:
    """Retrieve ranked evidence for a normalized lesson request (soft-degrading)."""
    limit = limit or settings.rag_top_k
    query, standards, filters = _build_query(request)
    if not query:
        return RetrievalReport(mode="none")
    try:
        chunks, mode, embed_error = await _search(
            db, query, standards=standards, filters=filters, limit=limit
        )
        return RetrievalReport(
            evidence=[c.as_dict() for c in chunks],
            mode=mode,
            degraded=embed_error is not None,
            error=embed_error,
        )
    except Exception as exc:  # noqa: BLE001 - retrieval is best-effort; never fail generation
        logger.warning("RAG retrieval failed; continuing without evidence: %s", exc)
        return RetrievalReport(mode="none", degraded=True, error=str(exc))
