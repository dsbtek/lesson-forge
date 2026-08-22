"""RAG is gated off by default; the gates reflect settings (README §10).

Mirrors the LLM provider's offline gate: with `rag_enabled` false (the default and
the test environment), the worker performs no retrieval and no embeddings are
produced, so the whole suite runs without a DB or Ollama.
"""

from __future__ import annotations

from app.rag import embeddings, retrieval


def test_retrieval_unavailable_by_default():
    assert retrieval.available() is False


def test_embeddings_disabled_by_default():
    assert embeddings.enabled() is False


def test_retrieval_available_tracks_rag_enabled(monkeypatch):
    monkeypatch.setattr(retrieval.settings, "rag_enabled", True)
    assert retrieval.available() is True
    monkeypatch.setattr(retrieval.settings, "rag_enabled", False)
    assert retrieval.available() is False


def test_embeddings_enabled_requires_flag_model_and_host(monkeypatch):
    monkeypatch.setattr(embeddings.settings, "rag_enabled", True)
    monkeypatch.setattr(embeddings.settings, "embedding_model", "nomic-embed-text")
    monkeypatch.setattr(embeddings.settings, "ollama_host", "http://ollama:11434")
    assert embeddings.enabled() is True

    # Any missing piece disables dense embeddings (retrieval falls back to sparse).
    monkeypatch.setattr(embeddings.settings, "embedding_model", "")
    assert embeddings.enabled() is False

    monkeypatch.setattr(embeddings.settings, "embedding_model", "nomic-embed-text")
    monkeypatch.setattr(embeddings.settings, "ollama_host", "")
    assert embeddings.enabled() is False

    monkeypatch.setattr(embeddings.settings, "ollama_host", "http://ollama:11434")
    monkeypatch.setattr(embeddings.settings, "rag_enabled", False)
    assert embeddings.enabled() is False
