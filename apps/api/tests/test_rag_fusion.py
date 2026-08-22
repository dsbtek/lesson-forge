"""Reciprocal Rank Fusion is pure and deterministic (app/rag/fusion.py).

No DB, no model — just the ranking math the hybrid retriever relies on.
"""

from __future__ import annotations

import pytest

from app.rag.fusion import DEFAULT_K, fuse_ranked, reciprocal_rank_fusion


def test_rank_contribution_matches_formula():
    # Single list: item at rank r contributes 1 / (k + r + 1).
    scores = reciprocal_rank_fusion([["a", "b", "c"]], k=DEFAULT_K)
    assert scores["a"] == pytest.approx(1 / (DEFAULT_K + 1))
    assert scores["b"] == pytest.approx(1 / (DEFAULT_K + 2))
    assert scores["c"] == pytest.approx(1 / (DEFAULT_K + 3))


def test_agreement_across_lists_wins():
    # 'b' is near the top of both lists; it should outrank singletons.
    scores = reciprocal_rank_fusion([["a", "b"], ["b", "c"]])
    assert scores["b"] > scores["a"]
    assert scores["b"] > scores["c"]


def test_only_first_occurrence_counts_within_a_list():
    scores = reciprocal_rank_fusion([["a", "a", "b"]], k=DEFAULT_K)
    # Second 'a' (rank 1) is ignored; 'b' keeps its rank-2 contribution.
    assert scores["a"] == pytest.approx(1 / (DEFAULT_K + 1))
    assert scores["b"] == pytest.approx(1 / (DEFAULT_K + 3))


def test_weights_scale_contributions():
    scores = reciprocal_rank_fusion([["a"], ["a"]], weights=[2.0, 3.0], k=DEFAULT_K)
    assert scores["a"] == pytest.approx(5 / (DEFAULT_K + 1))


def test_weights_length_must_match():
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([["a"]], weights=[1.0, 2.0])


def test_fuse_ranked_orders_best_first():
    ranked = fuse_ranked([["a", "b"], ["b", "c"]])
    items = [item for item, _ in ranked]
    assert items[0] == "b"  # agreement wins
    # Scores are monotonically non-increasing.
    values = [score for _, score in ranked]
    assert values == sorted(values, reverse=True)


def test_fuse_ranked_tie_break_is_deterministic():
    # Symmetric input → 'a' and 'b' tie on score; str() ordering breaks the tie.
    a = fuse_ranked([["b", "a"], ["a", "b"]])
    b = fuse_ranked([["a", "b"], ["b", "a"]])
    assert [i for i, _ in a] == [i for i, _ in b] == ["a", "b"]


def test_boosts_are_additive_and_only_apply_to_present_items():
    ranked = dict(fuse_ranked([["a", "b"]], boosts={"b": 1.0, "ghost": 5.0}))
    assert "ghost" not in ranked  # boost for an absent item is ignored
    assert ranked["b"] > ranked["a"]  # boost lifts 'b' above the higher-ranked 'a'
    assert ranked["b"] == pytest.approx(1 / (DEFAULT_K + 2) + 1.0)


def test_empty_input_yields_empty_result():
    assert reciprocal_rank_fusion([]) == {}
    assert fuse_ranked([]) == []
