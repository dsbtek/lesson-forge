"""rag indexes: hnsw vector index + embedding dimension normalization

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-22 00:00:00.000000

Phase 3 (Hybrid RAG). The initial migration created the sparse GIN index on
``content_tsv`` but no dense index. This adds an HNSW index with cosine ops on the
``embedding`` column (the "Index documents" checklist item), complementing the FTS
index so hybrid retrieval is fast on both signals.

It also normalizes the embedding column width to ``settings.embedding_dim`` (768 for
the default ``nomic-embed-text`` model). The column is empty until ingestion runs, so
``USING NULL`` is a safe, lossless reset here.

Requires pgvector ≥ 0.5 for HNSW (satisfied by the ``pgvector/pgvector:pg16`` image).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from app.config import settings

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Normalize the vector width to the configured embedding dimension. Safe because
    # the column holds no data before Phase 3 ingestion; drop the index first if any.
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding")
    op.execute(
        f"ALTER TABLE knowledge_chunks "
        f"ALTER COLUMN embedding TYPE vector({settings.embedding_dim}) USING NULL"
    )
    # Dense index for approximate nearest-neighbor search under cosine distance.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding "
        "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding")
