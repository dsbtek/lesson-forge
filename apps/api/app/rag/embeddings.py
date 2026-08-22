"""Dense embeddings via the host-run Ollama server (README §23 — "Generate embeddings").

Mirrors :mod:`app.services.llm`: the ``ollama`` package is imported lazily so the
offline path needs no dependency, and embeddings are only produced when
:func:`enabled` is true (``rag_enabled`` set *and* an ``embedding_model`` /
``ollama_host`` configured). Any provider failure raises :class:`EmbeddingError`;
callers in the retrieval/ingestion paths decide whether to soft-degrade (retrieval)
or fail (ingestion).

The embedding dimension must match ``settings.embedding_dim`` — the pgvector column
is fixed-width. With the default ``nomic-embed-text`` model that is 768.
"""

from __future__ import annotations

from app.config import settings


class EmbeddingError(RuntimeError):
    """Raised when an Ollama embedding call fails."""


def enabled() -> bool:
    """True when dense embeddings can be produced (else retrieval is sparse-only)."""
    return bool(settings.rag_enabled and settings.embedding_model and settings.ollama_host)


def _client():
    """Return a sync Ollama client. Imported lazily so offline paths need no dep."""
    import ollama

    return ollama.Client(host=settings.ollama_host, timeout=settings.llm_timeout)


def embed_texts(texts: list[str], *, model: str | None = None) -> list[list[float]]:
    """Embed a batch of texts, returning one vector per input (order preserved).

    Raises :class:`EmbeddingError` on any transport/protocol failure or if the
    provider returns a vector whose width does not match ``settings.embedding_dim``.
    """
    if not texts:
        return []
    try:
        response = _client().embed(model=model or settings.embedding_model, input=texts)
        raw = response.get("embeddings") if isinstance(response, dict) else response.embeddings
        vectors = list(raw)
    except Exception as exc:  # noqa: BLE001 - normalize every provider failure
        raise EmbeddingError(f"Ollama embedding failed: {exc}") from exc

    if len(vectors) != len(texts):
        raise EmbeddingError(f"expected {len(texts)} embeddings, got {len(vectors)}")
    dim = settings.embedding_dim
    for v in vectors:
        if len(v) != dim:
            raise EmbeddingError(
                f"embedding width {len(v)} != EMBEDDING_DIM {dim}; "
                f"check EMBEDDING_MODEL='{model or settings.embedding_model}'"
            )
    return [list(v) for v in vectors]


def embed_query(text: str, *, model: str | None = None) -> list[float]:
    """Embed a single query string into one vector."""
    return embed_texts([text], model=model)[0]
