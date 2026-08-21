"""Per-agent LLM output schemas (Phase 2).

Each generative agent constrains its Ollama output to one of these models, then
returns ``model_dump()``. They compose the shared lesson pieces in
``app/schemas/lesson.py`` so structured agent output stays aligned with the final
:class:`~app.schemas.lesson.LessonContent` contract.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.lesson import (
    Assessment,
    Differentiation,
    LessonSection,
    Objective,
    ReviewResult,
    StandardRef,
)


class NormalizedRequest(BaseModel):
    grade: str = ""
    subject: str = ""
    topic: str = ""
    duration_minutes: int = 60
    standards: list[str] = Field(default_factory=list)
    instructional_strategy: str | None = None
    learner_profiles: list[str] = Field(default_factory=list)
    assessment_type: str | None = None


class ResearchResult(BaseModel):
    standards: list[StandardRef] = Field(default_factory=list)
    learning_requirements: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)


class DesignOutput(BaseModel):
    objectives: list[Objective] = Field(default_factory=list)
    sections: list[LessonSection] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    vocabulary: list[str] = Field(default_factory=list)


class AssessmentResult(BaseModel):
    assessments: list[Assessment] = Field(default_factory=list)


# Aliases so each agent has a single, self-describing import site.
DifferentiationResult = Differentiation
CriticReview = ReviewResult

__all__ = [
    "NormalizedRequest",
    "ResearchResult",
    "DesignOutput",
    "AssessmentResult",
    "DifferentiationResult",
    "CriticReview",
]
