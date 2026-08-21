"""Assessment Specialist (README section 8.5).

Creates assessments aligned to objectives:
    Objective -> Activity -> Evidence of Learning -> Assessment
Uses an LLM when enabled; deterministic fallback otherwise. Assessment IDs are
assigned deterministically by the graph, so the agent leaves ``id`` empty.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents import prompts
from app.agents.io_schemas import AssessmentResult
from app.services import llm


def _user(request: dict[str, Any], draft: dict[str, Any]) -> str:
    return (
        "Assessment type requested: "
        + json.dumps(request.get("assessment_type"))
        + "\n\nObjectives and sections to assess:\n"
        + json.dumps(draft, indent=2, default=str)
    )


def assess(request: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    if llm.enabled():
        return llm.generate_structured(
            prompts.ASSESSMENT_SYSTEM, _user(request, draft), AssessmentResult
        ).model_dump()
    return _fallback(request, draft)


def _fallback(request: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    topic = request.get("topic") or request.get("subject") or "the topic"
    return {
        "assessments": [
            {
                "id": "assessment-1",
                "type": "exit_ticket",
                "questions": [f"Explain one key idea you learned about {topic}."],
                "success_criteria": [
                    "Response references a lesson concept.",
                    "Explanation is accurate and in the student's own words.",
                ],
            }
        ]
    }
