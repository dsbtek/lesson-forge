"""Assessment Specialist (README section 8.5).

Creates assessments aligned to objectives:
    Objective -> Activity -> Evidence of Learning -> Assessment
TODO(phase2): generate items + rubrics with an LLM and verify alignment.
"""

from __future__ import annotations

from typing import Any


def assess(request: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
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
