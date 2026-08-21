"""Unit tests for the Ollama LLM provider (app/services/llm.py).

These never touch a real Ollama server: the client is faked. They assert the
offline gate, the schema-constrained call shape, and error normalization.
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


class _FakeClient:
    def __init__(self, content: str) -> None:
        self._content = content
        self.calls: list[dict] = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeResponse(self._content)


def test_enabled_reflects_settings(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_enabled", False)
    assert llm.enabled() is False

    monkeypatch.setattr(llm.settings, "llm_enabled", True)
    monkeypatch.setattr(llm.settings, "ollama_host", "http://ollama:11434")
    assert llm.enabled() is True

    # No host configured → disabled even when the flag is on.
    monkeypatch.setattr(llm.settings, "ollama_host", "")
    assert llm.enabled() is False


def test_generate_structured_builds_call_and_parses(monkeypatch):
    fake = _FakeClient('{"name": "hi", "n": 3}')
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
    class _Boom:
        def chat(self, **kwargs):
            raise RuntimeError("connection refused")

    monkeypatch.setattr(llm, "_client", lambda: _Boom())
    with pytest.raises(llm.LLMError):
        llm.generate_structured("s", "u", _Out)
