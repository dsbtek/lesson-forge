"""Hybrid RAG layer (README §10).

Turns the Curriculum Researcher from a stub into an evidence-grounded agent:

    ingest (chunk → embed → index)  ──►  knowledge_chunks
                                             │
    request ──► retrieve (dense ⊕ sparse ⊕ RRF) ──► ranked evidence ──► researcher

Everything is gated behind ``settings.rag_enabled`` (default false), mirroring
``app.services.llm``: with RAG disabled the worker performs no retrieval and the
researcher falls back to its deterministic output, so the app and tests run offline.

Submodules:
  - :mod:`app.rag.embeddings` — Ollama embeddings (dense vectors).
  - :mod:`app.rag.chunking`   — deterministic text chunker.
  - :mod:`app.rag.fusion`     — reciprocal rank fusion (pure).
  - :mod:`app.rag.loaders`    — document loaders (jsonl/txt/md/pdf/html).
  - :mod:`app.rag.retrieval`  — the hybrid retriever used by the worker.
  - :mod:`app.rag.ingest`     — ingestion CLI (``python -m app.rag.ingest``).
"""

from __future__ import annotations
