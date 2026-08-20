"""LangGraph pipeline (README section 6 agent graph).

Wires the agent stubs into a compiled ``StateGraph`` over ``LessonState``:

    normalize -> research -> design -> (differentiate ∥ assess) -> critic
              -> validate -> finalize

The differentiation and assessment steps fan out from the designer and fan back
into the critic. Nodes are deterministic stubs today; the repair loop (README
section 11) is a Phase 2 follow-up.
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
    "finalize": "finalizer",
}


def _node_normalize(state: LessonState) -> dict:
    return {"request": normalizer.normalize(state.get("request", {})), "status": "normalized"}


def _node_research(state: LessonState) -> dict:
    return {"research": researcher.research(state["request"])}


def _node_design(state: LessonState) -> dict:
    return {"draft": designer.design(state["request"], state.get("research", {}))}


def _node_differentiate(state: LessonState) -> dict:
    return {
        "differentiation": differentiation.differentiate(state["request"], state.get("draft", {}))
    }


def _node_assess(state: LessonState) -> dict:
    return {"assessment": assessment.assess(state["request"], state.get("draft", {}))}


def _node_critic(state: LessonState) -> dict:
    return {"review": critic.review(state)}


def _node_validate(state: LessonState) -> dict:
    v = validator.validate(
        state.get("draft", {}),
        state.get("assessment", {}),
        int(state["request"].get("duration_minutes", 60)),
    )
    return {"validation": v}


def _node_finalize(state: LessonState) -> dict:
    return {"final_content": finalizer.finalize(state), "status": "completed"}


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
    g.add_edge("validate", "finalize")
    g.add_edge("finalize", END)
    return g.compile()


@lru_cache
def get_graph():
    """Return a cached compiled graph."""
    return build_graph()
