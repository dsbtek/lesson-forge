# knowledge/

Source curriculum documents and standards corpora (NGSS, Common Core, state
frameworks, etc.) used to seed the hybrid-RAG `knowledge_chunks` table.

Ingestion (chunking → embedding → upsert into pgvector + FTS) is a Phase 2/3
follow-up. In Phase 1 the `knowledge_chunks` schema and pgvector wiring exist, but
this directory is empty and retrieval is stubbed.
