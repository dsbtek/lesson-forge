"""Input Normalizer (README section 8.1).

Converts free-form teacher input into a canonical request.
TODO(phase2): use an LLM to parse messy natural-language input + detect gaps.
"""

from __future__ import annotations

from typing import Any


def normalize(request: dict[str, Any]) -> dict[str, Any]:
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
