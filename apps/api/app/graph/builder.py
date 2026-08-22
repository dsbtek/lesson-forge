r"""LangGraph pipeline (README sections 6 and 11 — agent graph + repair loop).

Wires the agents into a compiled ``StateGraph`` over ``LessonState``:

    normalize -> research -> design -> (differentiate ∥ assess) -> critic
              -> validate --(ok)------> finalize
                          \--(repair)--> repair -> design   (loop)

The differentiation and assessment steps fan out from the designer and fan back
into the critic. After validation, ``route_after_validate`` sends the state to
``finalize`` when the lesson is valid and the critic score clears
``quality_threshold``; otherwise (and while ``revision < max_revisions``) it
routes through ``repair`` back to the designer for another attempt.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agents import (
    assessment,
    critic,
    designer,
    differentiation,
    finalizer,
    normalizer,
    researcher,
    validator,
)
from app.config import settings
from app.schemas.state import LessonState

# Ordered node keys with friendly labels (used for progress events).
NODE_LABELS: dict[str, str] = {
    "normalize": "input_normalizer",
    "research": "curriculum_researcher",
    "design": "instructional_designer",
    "differentiate": "differentiation_agent",
    "assess": "assessment_specialist",
    "critic": "critic_reviewer",
    "validate": "deterministic_validator",
    "repair": "repair_agent",
    "finalize": "finalizer",
}


def _node_normalize(state: LessonState) -> dict:
    return {"request": normalizer.normalize(state.get("request", {})), "status": "normalized"}


def _node_research(state: LessonState) -> dict:
    # Evidence is retrieved by the worker (async) and injected into the initial
    # state; offline / RAG-disabled runs pass no evidence and the researcher falls back.
    return {"research": researcher.research(state["request"], state.get("evidence") or [])}


def _node_design(state: LessonState) -> dict:
    return {
        "draft": designer.design(
            state["request"], state.get("research", {}), state.get("repair_notes")
        )
    }


def _node_differentiate(state: LessonState) -> dict:
    return {
        "differentiation": differentiation.differentiate(state["request"], state.get("draft", {}))
    }


def _node_assess(state: LessonState) -> dict:
    result = assessment.assess(state["request"], state.get("draft", {}))
    # Assign stable IDs regardless of provider so objectives can be linked to them.
    for i, item in enumerate(result.get("assessments", []), start=1):
        item["id"] = f"assessment-{i}"
    return {"assessment": result}


def _node_critic(state: LessonState) -> dict:
    return {"review": critic.review(state)}


def _node_validate(state: LessonState) -> dict:
    draft = validator.link_objectives_to_assessments(
        state.get("draft", {}), state.get("assessment", {})
    )
    v = validator.validate(
        draft,
        state.get("assessment", {}),
        int(state["request"].get("duration_minutes", 60)),
    )
    # Return the linked draft too, so finalize persists the reconciled version.
    return {"draft": draft, "validation": v}


def _node_repair(state: LessonState) -> dict:
    validation = state.get("validation", {})
    review = state.get("review", {})
    notes = list(validation.get("errors", []))
    notes += [issue.get("issue", "") for issue in review.get("issues", []) if issue.get("issue")]
    return {
        "repair_notes": notes,
        "revision": int(state.get("revision", 0)) + 1,
        "status": "repairing",
    }


def _node_finalize(state: LessonState) -> dict:
    return {"final_content": finalizer.finalize(state), "status": "completed"}


def route_after_validate(state: LessonState) -> str:
    """Decide whether to repair or finalize after validation (README §11)."""
    validation = state.get("validation", {})
    review = state.get("review", {})
    revision = int(state.get("revision", 0))

    needs_repair = (not validation.get("valid", True)) or (
        float(review.get("score", 1.0)) < settings.quality_threshold
    )
    if needs_repair and revision < settings.max_revisions:
        return "repair"
    return "finalize"


def build_graph():
    """Build and compile the lesson-generation graph."""
    g = StateGraph(LessonState)
    g.add_node("normalize", _node_normalize)
    g.add_node("research", _node_research)
    g.add_node("design", _node_design)
    g.add_node("differentiate", _node_differentiate)
    g.add_node("assess", _node_assess)
    g.add_node("critic", _node_critic)
    g.add_node("validate", _node_validate)
    g.add_node("repair", _node_repair)
    g.add_node("finalize", _node_finalize)

    g.add_edge(START, "normalize")
    g.add_edge("normalize", "research")
    g.add_edge("research", "design")
    # Fan out: differentiation and assessment run from the shared draft.
    g.add_edge("design", "differentiate")
    g.add_edge("design", "assess")
    # Fan in: the critic waits for both.
    g.add_edge("differentiate", "critic")
    g.add_edge("assess", "critic")
    g.add_edge("critic", "validate")
    # Reflection loop: repair routes back to the designer; otherwise finalize.
    g.add_conditional_edges(
        "validate", route_after_validate, {"repair": "repair", "finalize": "finalize"}
    )
    g.add_edge("repair", "design")
    g.add_edge("finalize", END)
    return g.compile()


@lru_cache
def get_graph():
    """Return a cached compiled graph."""
    return build_graph()
