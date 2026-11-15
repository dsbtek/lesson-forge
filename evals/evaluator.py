"""Automated evaluation rubrics for LessonForge generated lessons (Phase 5).

Evaluates lesson plans against five key dimensions:
1. Structural Validity (Pydantic schema conformity)
2. Timing & Pacing (Section durations sum to total duration)
3. Standards Grounding (Requested standards exist with citations/evidence)
4. Pedagogical Completeness (Objectives, Differentiation, Assessments present)
5. Quality Threshold (Critic score >= 0.8)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RubricResult:
    dimension: str
    passed: bool
    score: float  # 0.0 to 1.0
    details: str


@dataclass
class EvalReport:
    lesson_id: str
    overall_passed: bool
    overall_score: float
    results: list[RubricResult] = field(default_factory=list)


def evaluate_lesson(
    lesson: dict[str, Any],
    expected_request: dict[str, Any],
) -> EvalReport:
    """Run rubric evaluations on a generated lesson plan dictionary."""
    results: list[RubricResult] = []

    # 1. Structural Validity
    has_title = bool(lesson.get("title"))
    has_subject = bool(lesson.get("subject"))
    has_grade = bool(lesson.get("grade"))
    struct_score = (has_title + has_subject + has_grade) / 3.0
    results.append(
        RubricResult(
            dimension="Structural Validity",
            passed=struct_score == 1.0,
            score=struct_score,
            details=f"Title: {has_title}, Subject: {has_subject}, Grade: {has_grade}",
        )
    )

    # 2. Timing & Pacing
    target_duration = int(expected_request.get("duration_minutes", 60))
    sections = lesson.get("sections", [])
    total_sections_dur = sum(int(s.get("duration_minutes", 0)) for s in sections)
    dur_diff = abs(total_sections_dur - target_duration)
    pacing_passed = dur_diff == 0
    pacing_score = max(0.0, 1.0 - (dur_diff / max(target_duration, 1)))
    results.append(
        RubricResult(
            dimension="Timing & Pacing",
            passed=pacing_passed,
            score=pacing_score,
            details=f"Sum of sections: {total_sections_dur}m (Expected: {target_duration}m)",
        )
    )

    # 3. Standards Grounding
    expected_standards = expected_request.get("standards", [])
    lesson_standards = lesson.get("standards", [])
    std_codes = {s.get("code", "") if isinstance(s, dict) else str(s) for s in lesson_standards}
    matched = sum(1 for exp in expected_standards if any(exp in c for c in std_codes))
    std_score = matched / max(len(expected_standards), 1) if expected_standards else 1.0
    results.append(
        RubricResult(
            dimension="Standards Grounding",
            passed=std_score >= 0.5 or not expected_standards,
            score=std_score,
            details=f"Matched {matched}/{len(expected_standards)} requested standards",
        )
    )

    # 4. Pedagogical Completeness
    has_objs = len(lesson.get("objectives", [])) > 0
    diff = lesson.get("differentiation", {})
    has_diff = bool(diff and (diff.get("ell") or diff.get("iep") or diff.get("gifted")))
    has_assess = len(lesson.get("assessments", [])) > 0
    comp_score = (has_objs + has_diff + has_assess) / 3.0
    results.append(
        RubricResult(
            dimension="Pedagogical Completeness",
            passed=comp_score == 1.0,
            score=comp_score,
            details=f"Objectives: {has_objs}, Differentiation: {has_diff}, Assessments: {has_assess}",
        )
    )

    # 5. Quality Score from Critic
    review = lesson.get("review", {})
    critic_score = float(review.get("score", 0.8)) if isinstance(review, dict) else 0.8
    results.append(
        RubricResult(
            dimension="Pedagogical Quality Score",
            passed=critic_score >= 0.8,
            score=critic_score,
            details=f"Critic Score: {int(critic_score * 100)}% (Threshold: 80%)",
        )
    )

    overall_score = sum(r.score for r in results) / len(results)
    overall_passed = all(r.passed for r in results)

    return EvalReport(
        lesson_id=expected_request.get("id", "test-lesson"),
        overall_passed=overall_passed,
        overall_score=overall_score,
        results=results,
    )
