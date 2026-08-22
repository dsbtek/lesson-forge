"""The Curriculum Researcher grounds standards in retrieved evidence and never
invents one (app/agents/researcher.py, README §8.2).

All offline: the LLM is forced off, so these exercise the deterministic evidence
path and the unchanged no-evidence fallback.
"""

from __future__ import annotations

import pytest

from app.agents import researcher
from app.agents.io_schemas import ResearchResult
from app.services import llm

REQUEST = {
    "grade": "5",
    "subject": "Science",
    "topic": "Earth Systems",
    "duration_minutes": 60,
    "standards": ["5-ESS2-1"],
}

EVIDENCE = [
    {
        "id": "c1",
        "source": "NGSS",
        "content": "NGSS 5-ESS2-1 — Develop a model of Earth's interacting systems.",
        "meta": {
            "code": "5-ESS2-1",
            "framework": "NGSS",
            "section": "Performance Expectations",
            "authority_level": "official",
        },
        "score": 0.91,
    }
]


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_enabled", False)


def test_no_evidence_is_schema_valid_fallback():
    result = researcher.research(REQUEST)
    ResearchResult.model_validate(result)
    assert result["evidence"] == []
    assert result["citations"] == []
    # Fallback marks the standard as a stub rather than inventing a description.
    assert "pending retrieval" in result["standards"][0]["description"]


def test_evidence_grounds_matching_standard():
    result = researcher.research(REQUEST, EVIDENCE)
    ResearchResult.model_validate(result)

    (std,) = result["standards"]
    assert std["code"] == "5-ESS2-1"
    assert std["description"] == EVIDENCE[0]["content"]  # grounded, not a stub
    assert std["evidence"] == [EVIDENCE[0]["content"]]

    assert result["evidence"] == [EVIDENCE[0]["content"]]
    assert "NGSS 5-ESS2-1" in result["citations"]  # citation uses the code


def test_unmatched_standard_is_not_invented():
    request = {**REQUEST, "standards": ["99-ZZ9-9"]}
    result = researcher.research(request, EVIDENCE)
    ResearchResult.model_validate(result)

    (std,) = result["standards"]
    assert std["code"] == "99-ZZ9-9"
    assert std["description"] is None  # no authoritative evidence → no description
    assert std["evidence"] == []


def test_citation_falls_back_to_section_without_a_code():
    evidence = [
        {
            "id": "c2",
            "source": "StateFramework",
            "content": "Local pacing guidance for Earth systems.",
            "meta": {"section": "Unit 3"},
            "score": 0.4,
        }
    ]
    result = researcher.research(REQUEST, evidence)
    assert "StateFramework: Unit 3" in result["citations"]


def test_duplicate_evidence_is_deduplicated():
    dupes = EVIDENCE + [dict(EVIDENCE[0], id="c1-again")]
    result = researcher.research(REQUEST, dupes)
    assert result["evidence"] == [EVIDENCE[0]["content"]]
    assert len(result["citations"]) == 1
