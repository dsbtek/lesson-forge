"""LangGraph shared state.

A ``TypedDict`` (LangGraph's native state container) mirroring the README
shared-graph-state class diagram (section 9). Nodes return partial updates.
"""

from __future__ import annotations

from typing import Any, TypedDict


class LessonState(TypedDict, total=False):
    generation_id: str
    lesson_id: str
    request: dict[str, Any]
    research: dict[str, Any]
    draft: dict[str, Any]
    differentiation: dict[str, Any]
    assessment: dict[str, Any]
    review: dict[str, Any]
    validation: dict[str, Any]
    final_content: dict[str, Any]
    history: list[dict[str, Any]]
    revision: int
    repair_notes: list[str]
    status: str
