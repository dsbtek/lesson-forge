"""Reciprocal Rank Fusion (README §10 — "Reciprocal Rank Fusion / Reranker").

Pure, dependency-free, and deterministic so it can be unit-tested offline. RRF
combines several ranked lists of item ids into a single ranking without needing
comparable scores across retrievers: an item at rank ``r`` (0-based) in a list
contributes ``1 / (k + r + 1)`` to its fused score. Items appearing near the top
of multiple lists rise to the top of the fused result.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TypeVar

T = TypeVar("T")

DEFAULT_K = 60


def reciprocal_rank_fusion(
    ranked_lists: Iterable[Sequence[T]],
    *,
    k: int = DEFAULT_K,
    weights: Sequence[float] | None = None,
) -> dict[T, float]:
    """Fuse ranked lists into ``{item: score}`` (higher is better).

    Args:
        ranked_lists: each an ordered sequence of item ids (best first). Ids may
            repeat across lists; within one list only the first occurrence counts.
        k: RRF damping constant. Larger ``k`` flattens the contribution curve.
        weights: optional per-list multipliers (e.g. to boost dense over sparse).
            Must match the number of lists when provided.

    Returns:
        Mapping of item id to fused score. Iterate ``sorted(..., key=score, reverse=True)``
        to get the ranking.
    """
    lists = [list(rl) for rl in ranked_lists]
    if weights is not None and len(weights) != len(lists):
        raise ValueError(f"weights ({len(weights)}) must match ranked_lists ({len(lists)})")

    scores: dict[T, float] = {}
    for i, ranked in enumerate(lists):
        weight = 1.0 if weights is None else weights[i]
        seen: set[T] = set()
        for rank, item in enumerate(ranked):
            if item in seen:  # first (best) occurrence in this list only
                continue
            seen.add(item)
            scores[item] = scores.get(item, 0.0) + weight / (k + rank + 1)
    return scores


def fuse_ranked(
    ranked_lists: Iterable[Sequence[T]],
    *,
    k: int = DEFAULT_K,
    weights: Sequence[float] | None = None,
    boosts: dict[T, float] | None = None,
) -> list[tuple[T, float]]:
    """Return items ordered by fused score, best first.

    ``boosts`` is an optional additive per-item adjustment applied after fusion
    (used for authority boosting — see :mod:`app.rag.retrieval`). Ties break on a
    stable ordering of the item id's ``str`` form for determinism.
    """
    scores = reciprocal_rank_fusion(ranked_lists, k=k, weights=weights)
    if boosts:
        for item, bonus in boosts.items():
            if item in scores:
                scores[item] += bonus
    return sorted(scores.items(), key=lambda kv: (-kv[1], str(kv[0])))
