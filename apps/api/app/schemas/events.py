"""Streaming event schema and canonical event types (README section 12)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EventType(StrEnum):
    GENERATION_STARTED = "generation.started"
    AGENT_STARTED = "agent.started"
    AGENT_PROGRESS = "agent.progress"
    AGENT_COMPLETED = "agent.completed"
    RETRIEVAL_STARTED = "retrieval.started"
    RETRIEVAL_COMPLETED = "retrieval.completed"
    VALIDATION_STARTED = "validation.started"
    VALIDATION_FAILED = "validation.failed"
    REPAIR_STARTED = "repair.started"
    REPAIR_COMPLETED = "repair.completed"
    GENERATION_COMPLETED = "generation.completed"
    GENERATION_FAILED = "generation.failed"


# Terminal events that close an SSE stream.
TERMINAL_EVENTS = {EventType.GENERATION_COMPLETED, EventType.GENERATION_FAILED}


class StreamEvent(BaseModel):
    event: EventType
    generation_id: str
    agent: str | None = None
    message: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    data: dict[str, Any] = Field(default_factory=dict)
