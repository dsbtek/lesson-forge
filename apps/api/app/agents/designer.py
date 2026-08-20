"""Instructional Designer (README section 8.3).

Builds the core lesson structure as structured data. The stub lays out a 5E
sequence whose section durations sum exactly to the requested lesson duration,
so the deterministic validator passes.
TODO(phase2): generate objectives/sections with an LLM grounded in research.
"""

from __future__ import annotations

from typing import Any

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


def design(request: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
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
            "assessment_ids": ["assessment-1"],
        }
    ]

    return {
        "objectives": objectives,
        "sections": sections,
        "materials": ["Chart paper", "Student notebooks"],
        "vocabulary": [],
    }
