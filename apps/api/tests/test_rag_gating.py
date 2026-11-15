"""RAG is gated off by default; the gates reflect settings (README §10).

Mirrors the LLM provider's offline gate: with `rag_enabled` false (the default and
the test environment), the worker performs no retrieval and no embeddings are
produced, so the whole suite runs without a DB or model server.
"""

from __future__ import annotations

import pytest

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


def test_embeddings_enabled_openai_compat(monkeypatch):
    monkeypatch.setattr(embeddings.settings, "llm_provider", "openai_compat")
    monkeypatch.setattr(embeddings.settings, "rag_enabled", True)
    monkeypatch.setattr(embeddings.settings, "embedding_model", "all-minilm-l6-v2")
    monkeypatch.setattr(embeddings.settings, "ai_base_url", "http://localhost:8080/v1")
    assert embeddings.enabled() is True

    monkeypatch.setattr(embeddings.settings, "ai_base_url", "")
    assert embeddings.enabled() is False


def test_embeddings_enabled_requires_flag_model_and_host_ollama(monkeypatch):
    monkeypatch.setattr(embeddings.settings, "llm_provider", "ollama")
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


def test_embed_texts_openai_compat_orders_and_validates_dim(monkeypatch):
    class _FakeHttpResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": [
                    {"index": 1, "embedding": [0.2] * 384},
                    {"index": 0, "embedding": [0.1] * 384},
                ]
            }

    class _FakeHttpClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, path, *, json):
            assert path == "/embeddings"
            assert json["model"] == "all-minilm-l6-v2"
            return _FakeHttpResponse()

    monkeypatch.setattr(embeddings.settings, "llm_provider", "openai_compat")
    monkeypatch.setattr(embeddings.settings, "embedding_model", "all-minilm-l6-v2")
    monkeypatch.setattr(embeddings.settings, "embedding_dim", 384)
    monkeypatch.setattr(embeddings, "_http_client", lambda: _FakeHttpClient())

    vectors = embeddings.embed_texts(["first", "second"])
    assert len(vectors) == 2
    assert vectors[0][0] == pytest.approx(0.1)
    assert vectors[1][0] == pytest.approx(0.2)
