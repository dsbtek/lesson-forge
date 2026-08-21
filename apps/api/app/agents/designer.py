"""Instructional Designer (README section 8.3).

Builds the core lesson structure as structured data. Uses an LLM when enabled;
otherwise a deterministic 5E fallback whose section durations sum exactly to the
requested duration. Accepts repair notes so the reflection loop (README §11) can
steer a re-design.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents import prompts
from app.agents.io_schemas import DesignOutput
from app.services import llm

_5E = [
    ("engage", "Engage / Hook"),
    ("explore", "Explore / Investigation"),
    ("explain", "Explain / Direct Instruction"),
    ("elaborate", "Elaborate / Guided Practice"),
    ("evaluate", "Evaluate / Closure"),
]


def _split_duration(total: int, n: int) -> list[int]:
    """Split ``total`` minutes across ``n`` sections summing exactly to total."""
    base = total // n
    durations = [base] * n
    for i in range(total - base * n):
        durations[i] += 1
    return durations


def _user(request: dict[str, Any], research: dict[str, Any], repair_notes: list[str] | None) -> str:
    total = int(request.get("duration_minutes", 60))
    parts = [
        "Design a lesson for this request:\n" + json.dumps(request, indent=2, default=str),
        "Curriculum research:\n" + json.dumps(research, indent=2, default=str),
        f"Section durations MUST sum to exactly {total} minutes.",
    ]
    if repair_notes:
        parts.append("Fix these issues from the previous attempt:\n- " + "\n- ".join(repair_notes))
    return "\n\n".join(parts)


def design(
    request: dict[str, Any],
    research: dict[str, Any],
    repair_notes: list[str] | None = None,
) -> dict[str, Any]:
    if llm.enabled():
        return llm.generate_structured(
            prompts.DESIGNER_SYSTEM, _user(request, research, repair_notes), DesignOutput
        ).model_dump()
    return _fallback(request, research)


def _fallback(request: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
    topic = request.get("topic") or request.get("subject") or "the topic"
    total = int(request.get("duration_minutes", 60))
    durations = _split_duration(total, len(_5E))

    sections = [
        {
            "id": sid,
            "title": title,
            "duration_minutes": dur,
            "teacher_actions": [f"Facilitate the {title.lower()} phase for {topic}."],
            "student_actions": [f"Participate in {title.lower()} activities about {topic}."],
            "materials": [],
        }
        for (sid, title), dur in zip(_5E, durations, strict=True)
    ]

    objectives = [
        {
            "id": "obj-1",
            "text": f"Students will investigate and explain key ideas about {topic}.",
            "assessment_ids": [],
        }
    ]

    return {
        "objectives": objectives,
        "sections": sections,
        "materials": ["Chart paper", "Student notebooks"],
        "vocabulary": [],
    }
