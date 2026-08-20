"""Pydantic schema validation tests (no DB required)."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.auth import UserCreate
from app.schemas.lesson import (
    ExportRequest,
    GenerateResponse,
    LessonContent,
    LessonRequest,
)


def test_lesson_request_valid():
    req = LessonRequest(
        grade="5",
        subject="Science",
        topic="Earth Systems",
        duration_minutes=60,
        standards=["NGSS 5-ESS2-1"],
        learner_profiles=["ELL", "Gifted"],
    )
    assert req.duration_minutes == 60
    assert req.standards == ["NGSS 5-ESS2-1"]
    # Optional fields default sensibly.
    assert req.instructional_strategy is None
    assert req.assessment_type is None


@pytest.mark.parametrize("bad_duration", [0, -10, 601])
def test_lesson_request_rejects_out_of_range_duration(bad_duration):
    with pytest.raises(ValidationError):
        LessonRequest(
            grade="5", subject="Science", topic="Earth", duration_minutes=bad_duration
        )


def test_lesson_request_requires_core_fields():
    with pytest.raises(ValidationError):
        LessonRequest(subject="Science", topic="Earth", duration_minutes=60)  # no grade


def test_user_create_rejects_short_password():
    with pytest.raises(ValidationError):
        UserCreate(email="teacher@example.com", password="short")


def test_user_create_rejects_bad_email():
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="a-long-enough-password")


def test_export_request_defaults_and_enum():
    assert ExportRequest().format == "pdf"
    with pytest.raises(ValidationError):
        ExportRequest(format="powerpoint")


def test_generate_response_serialization():
    resp = GenerateResponse(generation_id=uuid.uuid4(), lesson_id=uuid.uuid4())
    dumped = resp.model_dump()
    assert dumped["status"] == "queued"
    assert isinstance(dumped["generation_id"], uuid.UUID)


def test_lesson_content_minimal():
    content = LessonContent(
        title="Earth Systems", grade="5", subject="Science", duration_minutes=60
    )
    # Nested defaults are constructed.
    assert content.differentiation.ell == []
    assert content.review.review_passed is False
    assert content.sections == []
