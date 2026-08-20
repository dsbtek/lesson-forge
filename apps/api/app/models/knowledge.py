"""Knowledge chunk model — hybrid RAG substrate.

Combines a pgvector embedding column (dense/semantic retrieval) with a generated
``tsvector`` + GIN index (sparse/keyword retrieval). Ingestion and retrieval are
later-phase work; this model exists so the schema and pgvector wiring are in place.
"""

from __future__ import annotations

import uuid
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.db.base import Base, TimestampMixin, uuid_pk

EMBEDDING_DIM = settings.embedding_dim


class KnowledgeChunk(Base, TimestampMixin):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = uuid_pk()
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Arbitrary metadata for authority/framework/grade filtering (README section 10).
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    # Dense embedding; nullable until an embedding model is wired in.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    # Generated tsvector for sparse/keyword retrieval.
    content_tsv: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', content)", persisted=True)
    )

    __table_args__ = (
        Index(
            "ix_knowledge_chunks_content_tsv",
            "content_tsv",
            postgresql_using="gin",
        ),
    )
