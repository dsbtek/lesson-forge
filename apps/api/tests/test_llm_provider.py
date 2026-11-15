"""Unit tests for the LLM provider (app/services/llm.py).

These never touch a real model server: the client is faked. They assert the
offline gate, schema-constrained call shapes for both OpenAI-compatible
(llama.cpp) and Ollama providers, markdown fence stripping, and error
normalization.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from app.services import llm


class _Out(BaseModel):
    name: str
    n: int = 0


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeOllamaClient:
    def __init__(self, content: str) -> None:
        self._content = content
        self.calls: list[dict] = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeResponse(self._content)


class _FakeHttpResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeHttpClient:
    def __init__(self, content: str) -> None:
        self._content = content
        self.calls: list[tuple[str, dict]] = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, path: str, *, json: dict):
        self.calls.append((path, json))
        return _FakeHttpResponse({"choices": [{"message": {"content": self._content}}]})


def test_enabled_reflects_settings_openai_compat(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_provider", "openai_compat")
    monkeypatch.setattr(llm.settings, "llm_enabled", False)
    assert llm.enabled() is False

    monkeypatch.setattr(llm.settings, "llm_enabled", True)
    monkeypatch.setattr(llm.settings, "ai_base_url", "http://localhost:8080/v1")
    assert llm.enabled() is True

    monkeypatch.setattr(llm.settings, "ai_base_url", "")
    assert llm.enabled() is False


def test_enabled_reflects_settings_ollama(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_provider", "ollama")
    monkeypatch.setattr(llm.settings, "llm_enabled", False)
    assert llm.enabled() is False

    monkeypatch.setattr(llm.settings, "llm_enabled", True)
    monkeypatch.setattr(llm.settings, "ollama_host", "http://ollama:11434")
    assert llm.enabled() is True

    monkeypatch.setattr(llm.settings, "ollama_host", "")
    assert llm.enabled() is False


def test_generate_structured_openai_compat_builds_call_and_strips_fences(monkeypatch):
    fake = _FakeHttpClient('```json\n{"name": "hi", "n": 3}\n```')
    monkeypatch.setattr(llm.settings, "llm_provider", "openai_compat")
    monkeypatch.setattr(llm.settings, "llm_model", "qwen2.5-1.5b")
    monkeypatch.setattr(llm, "_http_client", lambda: fake)

    result = llm.generate_structured("SYS", "USER", _Out)

    assert isinstance(result, _Out)
    assert result.name == "hi"
    assert result.n == 3

    (path, payload), = fake.calls
    assert path == "/chat/completions"
    assert payload["model"] == "qwen2.5-1.5b"
    assert [m["role"] for m in payload["messages"]] == ["system", "user"]
    assert payload["messages"][0]["content"].startswith("SYS")
    assert payload["messages"][1]["content"] == "USER"
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["schema"] == _Out.model_json_schema()
    assert "max_tokens" in payload
    assert "temperature" in payload


def test_generate_structured_ollama_builds_call_and_parses(monkeypatch):
    fake = _FakeOllamaClient('{"name": "hi", "n": 3}')
    monkeypatch.setattr(llm.settings, "llm_provider", "ollama")
    monkeypatch.setattr(llm, "_client", lambda: fake)

    result = llm.generate_structured("SYS", "USER", _Out)

    assert isinstance(result, _Out)
    assert result.name == "hi"
    assert result.n == 3

    (call,) = fake.calls
    assert call["format"] == _Out.model_json_schema()
    assert [m["role"] for m in call["messages"]] == ["system", "user"]
    assert call["messages"][0]["content"] == "SYS"
    assert call["messages"][1]["content"] == "USER"
    assert "num_predict" in call["options"]
    assert "temperature" in call["options"]


def test_generate_structured_wraps_errors(monkeypatch):
    class _BoomHttp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            raise RuntimeError("connection refused")

    monkeypatch.setattr(llm.settings, "llm_provider", "openai_compat")
    monkeypatch.setattr(llm, "_http_client", lambda: _BoomHttp())
    with pytest.raises(llm.LLMError):
        llm.generate_structured("s", "u", _Out)

    class _BoomOllama:
        def chat(self, **kwargs):
            raise RuntimeError("connection refused")

    monkeypatch.setattr(llm.settings, "llm_provider", "ollama")
    monkeypatch.setattr(llm, "_client", lambda: _BoomOllama())
    with pytest.raises(llm.LLMError):
        llm.generate_structured("s", "u", _Out)
