"""embedding dim sync: resize knowledge_chunks.embedding to settings.embedding_dim

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-15 00:00:00.000000

Synchronizes the pgvector column width to ``settings.embedding_dim`` (384 for
the default ``all-minilm-l6-v2`` model, vs 768 for ``nomic-embed-text``) and
rebuilds the HNSW cosine index. Resets existing embeddings with ``USING NULL``
so switching embedding models only requires re-running ``make ingest``.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from app.config import settings

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding")
    op.execute(
        f"ALTER TABLE knowledge_chunks "
        f"ALTER COLUMN embedding TYPE vector({settings.embedding_dim}) USING NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding "
        "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding")
    op.execute(
        "ALTER TABLE knowledge_chunks "
        "ALTER COLUMN embedding TYPE vector(768) USING NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding "
        "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
    )

