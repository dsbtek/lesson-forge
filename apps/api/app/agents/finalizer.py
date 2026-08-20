"""Finalizer (README section 8 / output contract section 21).

Assembles the validated pieces into the canonical structured lesson JSON,
validating it through the ``LessonContent`` Pydantic model.
"""

from __future__ import annotations

from typing import Any

from app.schemas.lesson import LessonContent


def finalize(state: dict[str, Any]) -> dict[str, Any]:
    request = state.get("request", {})
    draft = state.get("draft", {})
    research = state.get("research", {})
    assessment = state.get("assessment", {})
    differentiation = state.get("differentiation", {})
    review = state.get("review", {})

    topic = request.get("topic") or request.get("subject") or "Lesson"

    content = LessonContent(
        title=f"Investigating {topic}",
        grade=str(request.get("grade", "")),
        subject=request.get("subject", ""),
        duration_minutes=int(request.get("duration_minutes", 60)),
        standards=research.get("standards", []),
        objectives=draft.get("objectives", []),
        sections=draft.get("sections", []),
        differentiation=differentiation or {},
        assessments=assessment.get("assessments", []),
        vocabulary=draft.get("vocabulary", []),
        materials=draft.get("materials", []),
        review=review or {},
    )
    return content.model_dump()
