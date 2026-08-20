"""Redis + ARQ connection helpers and event-stream conventions.

Generation progress is published to a Redis Stream per run
(``gen:{id}:events``); the SSE endpoint tails it and the worker appends to it.
"""

from __future__ import annotations

from arq.connections import ArqRedis, RedisSettings, create_pool
from redis.asyncio import Redis, from_url

from app.config import settings


def get_redis() -> Redis:
    """Return a text-mode async Redis client (caller is responsible for closing)."""
    return from_url(settings.redis_url, decode_responses=True)


def arq_redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.redis_url)


async def create_arq_pool() -> ArqRedis:
    """Create an ARQ pool for enqueueing jobs."""
    return await create_pool(arq_redis_settings())


def events_stream_key(generation_id: str) -> str:
    return f"gen:{generation_id}:events"
