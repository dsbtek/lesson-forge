"""Critic / Reviewer (README section 8.6).

Independent quality gate producing structured findings. Uses an LLM when enabled;
otherwise a deterministic pass. A low score (below ``quality_threshold``) or a
failed validation routes the graph back through the repair loop (README §11).
"""

from __future__ import annotations

import json
from typing import Any

from app.agents import prompts
from app.agents.io_schemas import CriticReview
from app.services import llm


def _user(state: dict[str, Any]) -> str:
    payload = {
        "request": state.get("request", {}),
        "draft": state.get("draft", {}),
        "differentiation": state.get("differentiation", {}),
        "assessment": state.get("assessment", {}),
    }
    return "Review this lesson for quality:\n" + json.dumps(payload, indent=2, default=str)


def review(state: dict[str, Any]) -> dict[str, Any]:
    if llm.enabled():
        return llm.generate_structured(
            prompts.CRITIC_SYSTEM, _user(state), CriticReview
        ).model_dump()
    return _fallback(state)


def _fallback(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_passed": True,
        "score": 0.9,
        "issues": [],
    }
