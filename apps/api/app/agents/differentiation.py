"""Differentiation Agent (README section 8.4).

Adds adaptations based on learner needs. Should modify the instructional
experience, not merely append a generic paragraph. Uses an LLM when enabled;
deterministic fallback otherwise.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents import prompts
from app.agents.io_schemas import DifferentiationResult
from app.services import llm


def _user(request: dict[str, Any], draft: dict[str, Any]) -> str:
    return (
        "Learner profiles: "
        + json.dumps(request.get("learner_profiles", []))
        + "\n\nLesson draft:\n"
        + json.dumps(draft, indent=2, default=str)
    )


def differentiate(request: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    if llm.enabled():
        return llm.generate_structured(
            prompts.DIFFERENTIATION_SYSTEM, _user(request, draft), DifferentiationResult
        ).model_dump()
    return _fallback(request, draft)


def _fallback(request: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    profiles = {p.lower() for p in request.get("learner_profiles", [])}
    return {
        "ell": (
            ["Provide sentence frames and a bilingual vocabulary list."]
            if "ell" in profiles
            else []
        ),
        "iep": (
            ["Offer chunked instructions and extended time."]
            if {"iep", "learning support", "struggling"} & profiles
            else []
        ),
        "gifted": (
            ["Add an open-ended extension challenge and a peer-teaching role."]
            if {"gifted", "advanced"} & profiles
            else []
        ),
    }
