"""Deterministic Validator (README sections 4.5 and 8.7).

Rules that can be computed are validated *without* an LLM. This is real logic,
not a stub: it catches issues like section durations that don't sum to the
lesson duration, or objectives with no matching assessment.
"""

from __future__ import annotations

from typing import Any


def validate(
    draft: dict[str, Any], assessment: dict[str, Any], duration_minutes: int
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    sections = draft.get("sections", [])
    objectives = draft.get("objectives", [])
    assessments = assessment.get("assessments", [])

    # Timing: section durations must sum to the requested lesson duration.
    total = sum(int(s.get("duration_minutes", 0)) for s in sections)
    if total != duration_minutes:
        errors.append(
            f"Section durations sum to {total} minutes but the lesson is {duration_minutes}."
        )

    # Structure: at least one section must exist.
    if not sections:
        errors.append("Lesson has no sections.")

    # Alignment: every objective must reference at least one existing assessment.
    assessment_ids = {a.get("id") for a in assessments}
    for obj in objectives:
        refs = obj.get("assessment_ids", [])
        if not refs:
            errors.append(f"Objective {obj.get('id')} has no assessment.")
        for ref in refs:
            if ref not in assessment_ids:
                errors.append(
                    f"Objective {obj.get('id')} references unknown assessment '{ref}'."
                )

    if not objectives:
        warnings.append("Lesson has no learning objectives.")

    return {"valid": not errors, "errors": errors, "warnings": warnings}
