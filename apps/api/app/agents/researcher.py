"""Curriculum Researcher (README section 8.2).

Primary agent for external factual grounding. Must never invent a standard when
authoritative evidence is unavailable. Uses an LLM when enabled; deterministic
fallback otherwise.
TODO(phase3): replace with hybrid RAG retrieval over indexed standards/curriculum.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents import prompts
from app.agents.io_schemas import ResearchResult
from app.services import llm


def _user(request: dict[str, Any]) -> str:
    return "Research curriculum grounding for this lesson request:\n" + json.dumps(
        request, indent=2, default=str
    )


def research(request: dict[str, Any]) -> dict[str, Any]:
    if llm.enabled():
        return llm.generate_structured(
            prompts.RESEARCHER_SYSTEM, _user(request), ResearchResult
        ).model_dump()
    return _fallback(request)


def _fallback(request: dict[str, Any]) -> dict[str, Any]:
    standards = request.get("standards", [])
    return {
        "standards": [
            {"code": code, "description": f"{code} (stub — pending retrieval)", "evidence": []}
            for code in standards
        ],
        "learning_requirements": [],
        "evidence": [],
        "citations": [],
    }
