"""Differentiation Agent (README section 8.4).

Adds adaptations based on learner needs. Should modify the instructional
experience, not merely append a generic paragraph.
TODO(phase2): generate profile-specific adaptations with an LLM.
"""

from __future__ import annotations

from typing import Any


def differentiate(request: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    profiles = {p.lower() for p in request.get("learner_profiles", [])}
    return {
        "ell": (
            ["Provide sentence frames and a bilingual vocabulary list."]
            if "ell" in profiles
            else []
        ),
        "iep": (
            ["Offer chunked instructions and extended time."]
            if {"iep", "learning support", "struggling"} & profiles
            else []
        ),
        "gifted": (
            ["Add an open-ended extension challenge and a peer-teaching role."]
            if {"gifted", "advanced"} & profiles
            else []
        ),
    }
