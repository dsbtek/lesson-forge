"""Curriculum Researcher (README section 8.2).

Primary agent for external factual grounding. Must never invent a standard when
authoritative evidence is unavailable.
TODO(phase3): replace with hybrid RAG retrieval over indexed standards/curriculum.
"""

from __future__ import annotations

from typing import Any


def research(request: dict[str, Any]) -> dict[str, Any]:
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
