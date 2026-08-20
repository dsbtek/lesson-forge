"""Critic / Reviewer (README section 8.6).

Independent quality gate producing structured findings. The stub returns a
passing review; a real critic would inspect alignment, coherence, timing, etc.
TODO(phase2): implement an LLM critic that emits scored, severity-tagged issues.
"""

from __future__ import annotations

from typing import Any


def review(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_passed": True,
        "score": 0.9,
        "issues": [],
    }
