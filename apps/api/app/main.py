"""FastAPI application factory.

Wires CORS, the v1 router, liveness/readiness probes, Prometheus metrics, and a
lifespan that manages the ARQ pool and disposes the DB engine on shutdown.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.api.v1.router import api_router
from app.config import settings
from app.db.session import async_session_factory, engine
from app.services.redis import create_arq_pool, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create the ARQ pool used to enqueue generation jobs.
    app.state.arq_pool = await create_arq_pool()
    try:
        yield
    finally:
        # Shutdown: close the pool and dispose the DB engine.
        await app.state.arq_pool.aclose()
        await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="LessonForge API",
        version="0.1.0",
        description="Agentic lesson-plan generator (Phase 1 foundation).",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def ready(response: Response) -> dict[str, str]:
        checks = {"database": "ok", "redis": "ok"}
        try:
            async with async_session_factory() as db:
                await db.execute(text("SELECT 1"))
        except Exception:  # noqa: BLE001
            checks["database"] = "error"
        redis = get_redis()
        try:
            await redis.ping()
        except Exception:  # noqa: BLE001
            checks["redis"] = "error"
        finally:
            await redis.aclose()

        if "error" in checks.values():
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return checks

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # /metrics for Prometheus (scraped by the observability profile).
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    return app


app = create_app()
