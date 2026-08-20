"""End-to-end execution of the (stubbed) LangGraph pipeline — no LLM, no DB.

Exercises the real graph wiring: fan-out (differentiate ∥ assess), fan-in at the
critic, and the deterministic validator. Confirms the stub pipeline produces a
self-consistent lesson (section durations sum to the requested total).
"""

from __future__ import annotations

from app.graph.builder import get_graph


def _request() -> dict:
    return {
        "grade": "5",
        "subject": "Science",
        "topic": "Earth Systems",
        "duration_minutes": 60,
        "standards": ["NGSS 5-ESS2-1"],
        "instructional_strategy": "Inquiry-based learning",
        "learner_profiles": ["ELL", "Gifted"],
        "assessment_type": "Formative + Exit Ticket",
    }


def test_graph_runs_to_completion():
    result = get_graph().invoke({"request": _request()})
    assert result["status"] == "completed"


def test_graph_produces_valid_lesson():
    result = get_graph().invoke({"request": _request()})
    validation = result["validation"]
    assert validation["valid"] is True, validation["errors"]


def test_graph_section_durations_sum_to_total():
    result = get_graph().invoke({"request": _request()})
    sections = result["final_content"]["sections"]
    assert sections, "expected the designer stub to produce sections"
    assert sum(s["duration_minutes"] for s in sections) == 60


def test_graph_fan_out_populated_both_branches():
    result = get_graph().invoke({"request": _request()})
    # Both parallel branches must have written to state before the critic ran.
    assert result["final_content"]["assessments"], "assessment branch empty"
    differentiation = result["final_content"]["differentiation"]
    assert any(differentiation.values()), "differentiation branch empty"
