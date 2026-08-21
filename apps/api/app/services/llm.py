"""LLM provider — local Ollama with schema-constrained structured output.

Agents call :func:`generate_structured` only when :func:`enabled` is true (the
``LLM_ENABLED`` setting *and* a configured ``OLLAMA_HOST``). Otherwise they use
their deterministic fallback, so the app, its tests, and a model-less
``docker compose up`` all work offline.

The ``ollama`` package is imported lazily inside the call, so it isn't required
for the offline path. When Ollama is enabled but the call fails (unreachable
server, bad JSON, schema mismatch) an :class:`LLMError` propagates so the worker
surfaces it as ``generation.failed`` rather than silently degrading.
"""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """Raised when a configured Ollama generation fails."""


def enabled() -> bool:
    """True when agents should call the LLM instead of their fallback."""
    return bool(settings.llm_enabled and settings.ollama_host)


def _client():
    """Return a sync Ollama client. Imported lazily so offline paths need no dep."""
    import ollama

    return ollama.Client(host=settings.ollama_host, timeout=settings.llm_timeout)


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

    Uses Ollama's schema-constrained decoding (``format=<json schema>``), then
    validates the returned text with the Pydantic model. Any failure — transport,
    protocol, or validation — is re-raised as :class:`LLMError`.
    """
    try:
        response = _client().chat(
            model=model or settings.llm_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            format=schema.model_json_schema(),
            options={
                "temperature": settings.llm_temperature if temperature is None else temperature,
                "num_predict": max_tokens or settings.llm_max_tokens,
            },
        )
        return schema.model_validate_json(response.message.content)
    except LLMError:
        raise
    except Exception as exc:  # noqa: BLE001 - normalize every provider failure
        raise LLMError(f"Ollama structured generation failed: {exc}") from exc
