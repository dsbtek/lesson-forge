-- Runs once on first Postgres container start (before Alembic).
-- Enables the extensions the hybrid RAG layer relies on:
--   vector  -> dense embedding search (pgvector)
--   pg_trgm -> trigram similarity to support keyword / FTS retrieval
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
