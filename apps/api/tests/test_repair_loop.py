"""The reflection / repair loop (README §11).

Covers the routing decision in isolation and an end-to-end run where the first
validation is forced to fail: the graph must loop back through repair → design,
then finalize once validation passes.
"""

from __future__ import annotations

from app.graph import builder


def _request() -> dict:
    return {
        "grade": "5",
        "subject": "Science",
        "topic": "Earth Systems",
        "duration_minutes": 60,
        "standards": ["NGSS 5-ESS2-1"],
        "learner_profiles": ["ELL", "Gifted"],
        "assessment_type": "Formative + Exit Ticket",
    }


def test_route_finalize_when_valid_and_high_score(monkeypatch):
    monkeypatch.setattr(builder.settings, "quality_threshold", 0.8)
    monkeypatch.setattr(builder.settings, "max_revisions", 2)
    state = {"validation": {"valid": True}, "review": {"score": 0.9}, "revision": 0}
    assert builder.route_after_validate(state) == "finalize"


def test_route_repair_when_invalid(monkeypatch):
    monkeypatch.setattr(builder.settings, "quality_threshold", 0.8)
    monkeypatch.setattr(builder.settings, "max_revisions", 2)
    state = {
        "validation": {"valid": False, "errors": ["x"]},
        "review": {"score": 0.9},
        "revision": 0,
    }
    assert builder.route_after_validate(state) == "repair"


def test_route_repair_when_low_score(monkeypatch):
    monkeypatch.setattr(builder.settings, "quality_threshold", 0.8)
    monkeypatch.setattr(builder.settings, "max_revisions", 2)
    state = {"validation": {"valid": True}, "review": {"score": 0.5}, "revision": 0}
    assert builder.route_after_validate(state) == "repair"


def test_route_finalize_when_budget_exhausted(monkeypatch):
    monkeypatch.setattr(builder.settings, "quality_threshold", 0.8)
    monkeypatch.setattr(builder.settings, "max_revisions", 2)
    state = {
        "validation": {"valid": False, "errors": ["x"]},
        "review": {"score": 0.1},
        "revision": 2,
    }
    assert builder.route_after_validate(state) == "finalize"


def test_repair_loop_runs_then_finalizes(monkeypatch):
    # Offline agents; a fresh (uncached) graph with a validator that fails once.
    monkeypatch.setattr(builder.settings, "llm_enabled", False)
    monkeypatch.setattr(builder.settings, "quality_threshold", 0.8)
    monkeypatch.setattr(builder.settings, "max_revisions", 2)

    calls = {"n": 0}
    real_validate = builder.validator.validate

    def flaky_validate(draft, assessment, duration):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"valid": False, "errors": ["forced failure"], "warnings": []}
        return real_validate(draft, assessment, duration)

    monkeypatch.setattr(builder.validator, "validate", flaky_validate)

    graph = builder.build_graph()
    result = graph.invoke({"request": _request(), "revision": 0})

    assert calls["n"] >= 2, "validator should run again after a repair"
    assert result.get("revision", 0) >= 1, "repair should increment the revision"
    assert result["status"] == "completed"
    assert result["validation"]["valid"] is True
