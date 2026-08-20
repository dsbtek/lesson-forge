"""Lesson and LessonVersion models (README ERD)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.export import Export
    from app.models.generation import GenerationRun
    from app.models.user import User


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(120), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(40), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    owner: Mapped[User] = relationship(back_populates="lessons")
    versions: Mapped[list[LessonVersion]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )
    generation_runs: Mapped[list[GenerationRun]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )


class LessonVersion(Base, TimestampMixin):
    __tablename__ = "lesson_versions"

    id: Mapped[uuid.UUID] = uuid_pk()
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # Canonical structured lesson JSON (README section 21 output contract).
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)

    lesson: Mapped[Lesson] = relationship(back_populates="versions")
    exports: Mapped[list[Export]] = relationship(
        back_populates="lesson_version", cascade="all, delete-orphan"
    )
