"""CLI evaluation harness runner (Phase 5).

Runs golden requests through the LessonForge LangGraph pipeline (or offline
fallback) and outputs an automated scorecard across all evaluation rubrics.

Usage:
  python3 -m evals.run_evals
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add apps/api to path so app modules can be loaded
API_DIR = Path(__file__).resolve().parent.parent / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.graph.builder import build_lesson_graph
from evals.evaluator import evaluate_lesson

FIXTURES_FILE = Path(__file__).resolve().parent / "fixtures" / "golden_lessons.json"


def main() -> int:
    print("=" * 70)
    print("LessonForge Automated Evaluation Suite (Phase 5 Hardening)")
    print("=" * 70)

    if not FIXTURES_FILE.exists():
        print(f"Error: Fixtures file not found at {FIXTURES_FILE}")
        return 1

    fixtures = json.loads(FIXTURES_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(fixtures)} golden curriculum fixtures.\n")

    graph = build_lesson_graph()
    total_score = 0.0
    passed_count = 0

    for fixture in fixtures:
        fid = fixture["id"]
        print(f"Running eval on [{fid}] ({fixture['grade']}th Grade {fixture['subject']})…")

        state_input = {
            "request": fixture,
            "revision": 0,
            "history": [],
            "retrieved_evidence": [],
        }

        # Run pipeline
        final_state = graph.invoke(state_input)
        content = final_state.get("final_lesson") or {}

        report = evaluate_lesson(content, fixture)
        total_score += report.overall_score
        if report.overall_passed:
            passed_count += 1

        status_str = "PASSED" if report.overall_passed else "FLAGGED"
        print(f"  Result: [{status_str}] Overall Score: {int(report.overall_score * 100)}%")
        for r in report.results:
            mark = "✓" if r.passed else "✗"
            print(f"    {mark} {r.dimension:<28}: {int(r.score * 100):>3}% | {r.details}")
        print()

    avg_score = total_score / len(fixtures) if fixtures else 0
    print("=" * 70)
    print(f"Summary: {passed_count}/{len(fixtures)} passed all rubrics.")
    print(f"Mean Pedagogical Quality Score: {int(avg_score * 100)}%")
    print("=" * 70)

    return 0 if passed_count == len(fixtures) else 1


if __name__ == "__main__":
    sys.exit(main())
