"""LLM provider — local OpenAI-compatible (llama.cpp) or Ollama structured output.

Agents call :func:`generate_structured` only when :func:`enabled` is true (the
``LLM_ENABLED`` setting *and* a configured provider endpoint). Otherwise they use
their deterministic fallback, so the app, its tests, and a model-less
``docker compose up`` all work offline.

Provider clients are imported/created lazily inside the call so offline paths
need no external runtime. When enabled but the call fails (unreachable server,
bad JSON, schema mismatch) an :class:`LLMError` propagates so the worker
surfaces it as ``generation.failed`` rather than silently degrading.
"""

from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel

from app.config import settings
from app.core.resilience import retry_with_backoff

T = TypeVar("T", bound=BaseModel)

_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)


class LLMError(RuntimeError):
    """Raised when a configured LLM generation fails."""


def enabled() -> bool:
    """True when agents should call the LLM instead of their fallback."""
    if not settings.llm_enabled:
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
    base_url = settings.ai_base_url.rstrip("/") + "/"
    return httpx.Client(
        base_url=base_url,
        headers=headers,
        timeout=settings.llm_timeout,
    )


def _strip_json_fences(raw: str) -> str:
    """Remove conversational text and markdown code fences around JSON output."""
    text = raw.strip()
    # Check for markdown code fences anywhere in the response
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    # Isolate JSON object if there is conversational preamble or suffix
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1]
    return text


def _generate_ollama(
    system: str,
    user: str,
    schema: type[T],
    model: str,
    max_tokens: int,
    temperature: float,
) -> T:
    response = _client().chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        format=schema.model_json_schema(),
        options={
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    )
    return schema.model_validate_json(response.message.content)


@retry_with_backoff(retries=2, initial_delay=0.5)
def _generate_openai_compat(
    system: str,
    user: str,
    schema: type[T],
    model: str,
    max_tokens: int,
    temperature: float,
) -> T:
    json_schema = schema.model_json_schema()
    schema_hint = (
        "\n\nRespond ONLY with a valid JSON object matching this JSON schema "
        "(no markdown fences, no extra text):\n"
        + json.dumps(json_schema)
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system + schema_hint},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    with _http_client() as client:
        resp = client.post("chat/completions", json=payload)
        # If the local router returns 400 rejecting response_format, retry without it
        if resp.status_code == 400 and "response_format" in resp.text:
            payload.pop("response_format", None)
            resp = client.post("chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return schema.model_validate_json(_strip_json_fences(content))


def generate_structured(
    system: str,
    user: str,
    schema: type[T],
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> T:
    """Generate a JSON object constrained to ``schema`` and validate it.

    Dispatches to the configured ``llm_provider`` (``openai_compat`` or
    ``ollama``), then validates the returned text with the Pydantic model. Any
    failure — transport, protocol, or validation — is re-raised as
    :class:`LLMError`.
    """
    target_model = model or settings.llm_model
    target_max_tokens = max_tokens or settings.llm_max_tokens
    target_temp = settings.llm_temperature if temperature is None else temperature

    try:
        if settings.llm_provider == "ollama":
            return _generate_ollama(
                system, user, schema, target_model, target_max_tokens, target_temp
            )
        return _generate_openai_compat(
            system, user, schema, target_model, target_max_tokens, target_temp
        )
    except LLMError:
        raise
    except Exception as exc:  # noqa: BLE001 - normalize every provider failure
        raise LLMError(
            f"{settings.llm_provider} structured generation failed: {exc}"
        ) from exc
