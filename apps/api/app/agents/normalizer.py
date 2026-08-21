"""Input Normalizer (README section 8.1).

Converts free-form teacher input into a canonical request. Uses an LLM when
enabled (see ``app/services/llm.py``); otherwise a deterministic fallback.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents import prompts
from app.agents.io_schemas import NormalizedRequest
from app.services import llm


def _user(request: dict[str, Any]) -> str:
    return "Normalize this teacher request:\n" + json.dumps(request, indent=2, default=str)


def normalize(request: dict[str, Any]) -> dict[str, Any]:
    if llm.enabled():
        return llm.generate_structured(
            prompts.NORMALIZER_SYSTEM, _user(request), NormalizedRequest
        ).model_dump()
    return _fallback(request)


def _fallback(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "grade": str(request.get("grade", "")),
        "subject": request.get("subject", ""),
        "topic": request.get("topic", ""),
        "duration_minutes": int(request.get("duration_minutes", 60)),
        "standards": list(request.get("standards", [])),
        "instructional_strategy": request.get("instructional_strategy"),
        "learner_profiles": list(request.get("learner_profiles", [])),
        "assessment_type": request.get("assessment_type"),
    }
