"""Dense embeddings via local OpenAI-compatible (llama.cpp) or Ollama server.

Mirrors :mod:`app.services.llm`: provider clients are created lazily so the
offline path needs no runtime dependency, and embeddings are only produced when
:func:`enabled` is true (``rag_enabled`` set, ``embedding_model`` configured,
and the provider endpoint set). Any provider failure raises
:class:`EmbeddingError`; callers in the retrieval/ingestion paths decide whether
to soft-degrade (retrieval) or fail (ingestion).

The embedding dimension must match ``settings.embedding_dim`` — the pgvector column
is fixed-width (384 for ``all-minilm-l6-v2``, 768 for ``nomic-embed-text``).
"""

from __future__ import annotations

from app.config import settings
from app.core.resilience import retry_with_backoff


class EmbeddingError(RuntimeError):
    """Raised when an embedding call fails."""


def enabled() -> bool:
    """True when dense embeddings can be produced (else retrieval is sparse-only)."""
    if not (settings.rag_enabled and settings.embedding_model):
        return False
    if settings.llm_provider == "ollama":
        return bool(settings.ollama_host)
    return bool(settings.ai_base_url)


def _client():
    """Return a sync Ollama client. Imported lazily so offline paths need no dep."""
    import ollama

    return ollama.Client(host=settings.ollama_host, timeout=settings.llm_timeout)


def _http_client():
    """Return a sync httpx client for OpenAI-compatible endpoints."""
    import httpx

    headers = {"Content-Type": "application/json"}
    if settings.ai_api_key:
        headers["Authorization"] = f"Bearer {settings.ai_api_key}"
    return httpx.Client(
        base_url=settings.ai_base_url.rstrip("/"),
        headers=headers,
        timeout=settings.llm_timeout,
    )


def _embed_ollama(texts: list[str], model: str) -> list[list[float]]:
    response = _client().embed(model=model, input=texts)
    raw = response.get("embeddings") if isinstance(response, dict) else response.embeddings
    return list(raw)


@retry_with_backoff(retries=2, initial_delay=0.5)
def _embed_openai_compat(texts: list[str], model: str) -> list[list[float]]:
    with _http_client() as client:
        resp = client.post("/embeddings", json={"model": model, "input": texts})
        resp.raise_for_status()
        data = resp.json()
    items = sorted(data["data"], key=lambda item: item["index"])
    return [item["embedding"] for item in items]


def embed_texts(texts: list[str], *, model: str | None = None) -> list[list[float]]:
    """Embed a batch of texts, returning one vector per input (order preserved).

    Raises :class:`EmbeddingError` on any transport/protocol failure or if the
    provider returns a vector whose width does not match ``settings.embedding_dim``.
    """
    if not texts:
        return []
    target_model = model or settings.embedding_model
    try:
        if settings.llm_provider == "ollama":
            vectors = _embed_ollama(texts, target_model)
        else:
            vectors = _embed_openai_compat(texts, target_model)
    except Exception as exc:  # noqa: BLE001 - normalize every provider failure
        raise EmbeddingError(f"{settings.llm_provider} embedding failed: {exc}") from exc

    if len(vectors) != len(texts):
        raise EmbeddingError(f"expected {len(texts)} embeddings, got {len(vectors)}")
    dim = settings.embedding_dim
    for v in vectors:
        if len(v) != dim:
            raise EmbeddingError(
                f"embedding width {len(v)} != EMBEDDING_DIM {dim}; "
                f"check EMBEDDING_MODEL='{target_model}'"
            )
    return [list(v) for v in vectors]


def embed_query(text: str, *, model: str | None = None) -> list[float]:
    """Embed a single query string into one vector."""
    return embed_texts([text], model=model)[0]
