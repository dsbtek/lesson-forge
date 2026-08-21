"""ARQ worker: runs the LangGraph pipeline and streams progress.

For each generation the worker:
  1. marks the GenerationRun running,
  2. streams the graph, emitting an AgentEvent row + a Redis Stream entry per node,
  3. persists a LessonVersion with the finalized content,
  4. emits a terminal generation.completed / generation.failed event.

No LLM calls happen yet — the graph nodes are deterministic stubs.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import func, select

from app.config import settings
from app.db.session import async_session_factory
from app.graph import NODE_LABELS, get_graph
from app.models import AgentEvent, GenerationRun, LessonVersion
from app.schemas.events import EventType, StreamEvent
from app.services.redis import arq_redis_settings, events_stream_key, get_redis


async def _emit(redis: Redis, db, generation_id: str, event: StreamEvent) -> None:
    """Publish an event to the Redis stream and persist it as an AgentEvent."""
    await redis.xadd(events_stream_key(generation_id), {"data": event.model_dump_json()})
    db.add(
        AgentEvent(
            generation_id=uuid.UUID(generation_id),
            agent=event.agent,
            event_type=str(event.event),
            payload=event.data,
        )
    )
    await db.commit()


async def _next_version(db, lesson_id: uuid.UUID) -> int:
    count = await db.scalar(
        select(func.count()).select_from(LessonVersion).where(LessonVersion.lesson_id == lesson_id)
    )
    return int(count or 0) + 1


async def run_generation(ctx: dict, generation_id: str, request: dict[str, Any]) -> dict[str, Any]:
    redis: Redis = ctx["stream_redis"]

    async with async_session_factory() as db:
        run = await db.get(GenerationRun, uuid.UUID(generation_id))
        if run is None:
            return {"error": f"generation run {generation_id} not found"}

        run.status = "running"
        run.started_at = datetime.now(UTC)
        await db.commit()

        await _emit(
            redis,
            db,
            generation_id,
            StreamEvent(
                event=EventType.GENERATION_STARTED,
                generation_id=generation_id,
                message="Starting generation",
            ),
        )

        try:
            graph = get_graph()
            initial: dict[str, Any] = {
                "request": request,
                "generation_id": generation_id,
                "lesson_id": str(run.lesson_id),
                "history": [],
                "revision": run.revision,
            }

            final_state: dict[str, Any] = {}
            total_nodes = len(NODE_LABELS)
            completed = 0

            # Allow the repair loop to revisit nodes without tripping the default
            # recursion limit (each revision replays design → … → validate).
            config = {"recursion_limit": settings.max_revisions * 10 + 10}

            async for update in graph.astream(initial, stream_mode="updates", config=config):
                for node_name, partial in update.items():
                    completed += 1
                    if partial:
                        final_state.update(partial)
                    label = NODE_LABELS.get(node_name, node_name)
                    progress = min(100, int(completed / total_nodes * 100))

                    if node_name == "repair":
                        data = {
                            "revision": partial.get("revision"),
                            "repair_notes": partial.get("repair_notes", []),
                        }
                        await _emit(
                            redis,
                            db,
                            generation_id,
                            StreamEvent(
                                event=EventType.REPAIR_STARTED,
                                generation_id=generation_id,
                                agent=label,
                                message="Repairing lesson after review",
                                data=data,
                            ),
                        )
                        await _emit(
                            redis,
                            db,
                            generation_id,
                            StreamEvent(
                                event=EventType.REPAIR_COMPLETED,
                                generation_id=generation_id,
                                agent=label,
                                message="Repair prepared; regenerating",
                                progress=progress,
                                data=data,
                            ),
                        )
                    else:
                        await _emit(
                            redis,
                            db,
                            generation_id,
                            StreamEvent(
                                event=EventType.AGENT_COMPLETED,
                                generation_id=generation_id,
                                agent=label,
                                message=f"{label} completed",
                                progress=progress,
                            ),
                        )

            validation = final_state.get("validation", {})
            if not validation.get("valid", True):
                await _emit(
                    redis,
                    db,
                    generation_id,
                    StreamEvent(
                        event=EventType.VALIDATION_FAILED,
                        generation_id=generation_id,
                        message="Deterministic validation failed",
                        data=validation,
                    ),
                )

            content = final_state.get("final_content", {})
            version_number = await _next_version(db, run.lesson_id)
            version = LessonVersion(
                lesson_id=run.lesson_id,
                version=version_number,
                content=content,
                status="final",
            )
            db.add(version)
            await db.flush()

            run.status = "completed"
            run.completed_at = datetime.now(UTC)
            run.quality_score = final_state.get("review", {}).get("score")
            await db.commit()

            await _emit(
                redis,
                db,
                generation_id,
                StreamEvent(
                    event=EventType.GENERATION_COMPLETED,
                    generation_id=generation_id,
                    message="Generation complete",
                    data={
                        "lesson_id": str(run.lesson_id),
                        "lesson_version_id": str(version.id),
                        "version": version_number,
                    },
                ),
            )
            return {"status": "completed", "lesson_version_id": str(version.id)}

        except Exception as exc:  # noqa: BLE001 - surface any failure to the client
            run.status = "failed"
            run.error = str(exc)[:2000]
            run.completed_at = datetime.now(UTC)
            await db.commit()
            await _emit(
                redis,
                db,
                generation_id,
                StreamEvent(
                    event=EventType.GENERATION_FAILED,
                    generation_id=generation_id,
                    message="Generation failed",
                    data={"error": str(exc)},
                ),
            )
            raise


async def on_startup(ctx: dict) -> None:
    ctx["stream_redis"] = get_redis()


async def on_shutdown(ctx: dict) -> None:
    redis: Redis | None = ctx.get("stream_redis")
    if redis is not None:
        await redis.aclose()


class WorkerSettings:
    """ARQ worker settings — referenced as ``app.workers.arq_worker.WorkerSettings``."""

    functions = [run_generation]
    redis_settings = arq_redis_settings()
    on_startup = on_startup
    on_shutdown = on_shutdown
