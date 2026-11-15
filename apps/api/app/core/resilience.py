"""Resilience & retry utilities with exponential backoff and jitter (Phase 5).

Protects against intermittent network timeouts, connection resets, and temporary
model provider unavailability.
"""

from __future__ import annotations

import asyncio
import functools
import random
import time
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


def retry_with_backoff(
    retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Synchronous decorator for retrying flaky calls with exponential backoff."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exc: Exception | None = None

            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == retries:
                        break
                    sleep_time = delay * (random.uniform(0.8, 1.2) if jitter else 1.0)
                    time.sleep(min(sleep_time, max_delay))
                    delay *= backoff_factor

            if last_exc:
                raise last_exc
            raise RuntimeError(f"{func.__name__} failed after {retries} retries.")

        return wrapper

    return decorator


def async_retry_with_backoff(
    retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[..., Any]:
    """Asynchronous decorator for retrying flaky calls with exponential backoff."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exc: Exception | None = None

            for attempt in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == retries:
                        break
                    sleep_time = delay * (random.uniform(0.8, 1.2) if jitter else 1.0)
                    await asyncio.sleep(min(sleep_time, max_delay))
                    delay *= backoff_factor

            if last_exc:
                raise last_exc
            raise RuntimeError(f"{func.__name__} failed after {retries} retries.")

        return wrapper

    return decorator
