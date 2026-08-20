"""GenerationRun and AgentEvent models (observability of a generation)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.lesson import Lesson


class GenerationRun(Base):
    __tablename__ = "generation_runs"

    id: Mapped[uuid.UUID] = uuid_pk()
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False)
    revision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    error: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    lesson: Mapped[Lesson] = relationship(back_populates="generation_runs")
    events: Mapped[list[AgentEvent]] = relationship(
        back_populates="generation_run", cascade="all, delete-orphan"
    )


class AgentEvent(Base, TimestampMixin):
    __tablename__ = "agent_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    generation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_runs.id", ondelete="CASCADE"), index=True
    )
    agent: Mapped[str | None] = mapped_column(String(120), nullable=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    generation_run: Mapped[GenerationRun] = relationship(back_populates="events")
