"""Lesson domain schemas — request, structured output contract, and reads.

Mirrors the README shared-state (section 9) and output-contract (section 21).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Input ─────────────────────────────────────────────────────
class LessonRequest(BaseModel):
    """Normalized teacher request that launches the agent graph."""

    grade: str = Field(examples=["5"])
    subject: str = Field(examples=["Science"])
    topic: str = Field(examples=["Earth Systems"])
    duration_minutes: int = Field(gt=0, le=600, examples=[60])
    standards: list[str] = Field(default_factory=list, examples=[["NGSS"]])
    instructional_strategy: str | None = Field(default=None, examples=["Inquiry-based learning"])
    learner_profiles: list[str] = Field(default_factory=list, examples=[["ELL", "Gifted"]])
    assessment_type: str | None = Field(default=None, examples=["Formative + Exit Ticket"])


# ── Structured lesson pieces (output contract) ────────────────
class StandardRef(BaseModel):
    code: str
    description: str | None = None
    evidence: list[str] = Field(default_factory=list)


class Objective(BaseModel):
    id: str
    text: str
    assessment_ids: list[str] = Field(default_factory=list)


class LessonSection(BaseModel):
    id: str
    title: str
    duration_minutes: int = 0
    teacher_actions: list[str] = Field(default_factory=list)
    student_actions: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)


class Differentiation(BaseModel):
    ell: list[str] = Field(default_factory=list)
    iep: list[str] = Field(default_factory=list)
    gifted: list[str] = Field(default_factory=list)


class Assessment(BaseModel):
    id: str
    type: str
    questions: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)


class ReviewIssue(BaseModel):
    severity: Literal["low", "medium", "high"] = "medium"
    field: str | None = None
    issue: str
    recommendation: str | None = None


class ReviewResult(BaseModel):
    review_passed: bool = False
    score: float = 0.0
    issues: list[ReviewIssue] = Field(default_factory=list)


class ValidationResult(BaseModel):
    valid: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class LessonContent(BaseModel):
    """The canonical structured lesson stored in ``LessonVersion.content``."""

    title: str
    grade: str
    subject: str
    duration_minutes: int
    standards: list[StandardRef] = Field(default_factory=list)
    objectives: list[Objective] = Field(default_factory=list)
    sections: list[LessonSection] = Field(default_factory=list)
    differentiation: Differentiation = Field(default_factory=Differentiation)
    assessments: list[Assessment] = Field(default_factory=list)
    vocabulary: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    review: ReviewResult = Field(default_factory=ReviewResult)


# ── API responses ─────────────────────────────────────────────
class GenerateResponse(BaseModel):
    generation_id: uuid.UUID
    lesson_id: uuid.UUID
    status: str = "queued"


class GenerationStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_id: uuid.UUID
    status: str
    revision: int
    quality_score: float | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class LessonVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: int
    status: str
    content: dict[str, Any]
    created_at: datetime


class LessonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    subject: str | None = None
    grade: str | None = None
    duration_minutes: int | None = None
    created_at: datetime


class LessonUpdate(BaseModel):
    title: str | None = None
    subject: str | None = None
    grade: str | None = None
    duration_minutes: int | None = None


class ExportRequest(BaseModel):
    format: Literal["docx", "pdf", "markdown", "google_docs", "lms"] = "pdf"
    version_id: uuid.UUID | None = None


class ExportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_version_id: uuid.UUID
    format: str
    status: str
    storage_url: str | None = None
    created_at: datetime
