"""Sliding-window rate limiter backed by Redis (Phase 5).

Protects expensive endpoints (e.g. lesson generation and export rendering)
from burst abuse. Soft-degrades gracefully if Redis is unavailable.
"""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.services.redis import get_redis


class RateLimiter:
    """Sliding-window rate limiter using Redis sorted sets (ZSET)."""

    def __init__(self, requests_per_window: int = 30, window_seconds: int = 60):
        self.requests = requests_per_window
        self.window = window_seconds

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        # Combine client IP with route path for granular limits
        key = f"ratelimit:{client_ip}:{request.url.path}"
        now = time.time()
        clear_before = now - self.window

        try:
            redis = get_redis()
            pipe = redis.pipeline()
            # Remove timestamps older than the sliding window
            pipe.zremrangebyscore(key, 0, clear_before)
            # Add current timestamp
            pipe.zadd(key, {str(now): now})
            # Count elements in current window
            pipe.zcard(key)
            # Set key expiry slightly longer than window
            pipe.expire(key, self.window + 5)
            results = await pipe.execute()
            await redis.aclose()

            count = results[2]
            if count > self.requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded ({self.requests} requests per {self.window}s). Please wait before retrying.",
                    headers={"Retry-After": str(self.window)},
                )
        except HTTPException:
            raise
        except Exception:
            # Soft-degrade gracefully if Redis is offline or fails
            return


# Standard rate limit dependency for generation endpoints
generation_rate_limit = Annotated[None, Depends(RateLimiter(requests_per_window=20, window_seconds=60))]
