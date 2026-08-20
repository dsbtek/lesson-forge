"""Export artifact model (DOCX / PDF / Markdown / LMS)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.lesson import LessonVersion


class Export(Base, TimestampMixin):
    __tablename__ = "exports"

    id: Mapped[uuid.UUID] = uuid_pk()
    lesson_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lesson_versions.id", ondelete="CASCADE"), index=True
    )
    format: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    storage_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    lesson_version: Mapped[LessonVersion] = relationship(back_populates="exports")
