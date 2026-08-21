"""Each agent's offline (deterministic fallback) output is schema-valid.

With the LLM disabled (the default), every agent must return data that validates
against its declared output schema, keeping the offline pipeline self-consistent.
"""

from __future__ import annotations

import pytest

from app.agents import (
    assessment,
    critic,
    designer,
    differentiation,
    normalizer,
    researcher,
)
from app.agents.io_schemas import (
    AssessmentResult,
    CriticReview,
    DesignOutput,
    DifferentiationResult,
    NormalizedRequest,
    ResearchResult,
)
from app.services import llm

REQUEST = {
    "grade": "5",
    "subject": "Science",
    "topic": "Earth Systems",
    "duration_minutes": 60,
    "standards": ["NGSS 5-ESS2-1"],
    "instructional_strategy": "Inquiry-based learning",
    "learner_profiles": ["ELL", "Gifted"],
    "assessment_type": "Formative + Exit Ticket",
}


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    """Force the deterministic fallback path for every agent."""
    monkeypatch.setattr(llm.settings, "llm_enabled", False)


def test_normalizer_offline():
    NormalizedRequest.model_validate(normalizer.normalize(REQUEST))


def test_researcher_offline():
    ResearchResult.model_validate(researcher.research(REQUEST))


def test_designer_offline_sums_to_duration():
    draft = designer.design(REQUEST, {})
    DesignOutput.model_validate(draft)
    assert sum(s["duration_minutes"] for s in draft["sections"]) == REQUEST["duration_minutes"]


def test_differentiation_offline():
    result = differentiation.differentiate(REQUEST, {})
    DifferentiationResult.model_validate(result)
    # ELL + Gifted profiles present → those adaptations populated.
    assert result["ell"] and result["gifted"]


def test_assessment_offline():
    AssessmentResult.model_validate(assessment.assess(REQUEST, {}))


def test_critic_offline():
    CriticReview.model_validate(critic.review({"request": REQUEST}))
