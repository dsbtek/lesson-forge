"""Generation endpoints: status polling and the SSE event stream."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, DbSession
from app.models import GenerationRun, Lesson
from app.schemas.events import TERMINAL_EVENTS
from app.schemas.lesson import GenerationStatus
from app.services.redis import events_stream_key, get_redis

router = APIRouter(prefix="/generations", tags=["generations"])

_TERMINAL = {str(e) for e in TERMINAL_EVENTS}


async def _get_owned_run(db: DbSession, generation_id: uuid.UUID, user_id: uuid.UUID) -> GenerationRun:
    run = await db.get(GenerationRun, generation_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation not found")
    lesson = await db.get(Lesson, run.lesson_id)
    if lesson is None or lesson.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation not found")
    return run


@router.get("/{generation_id}", response_model=GenerationStatus)
async def get_generation(
    generation_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> GenerationRun:
    return await _get_owned_run(db, generation_id, current_user.id)


@router.get("/{generation_id}/events")
async def stream_generation_events(
    generation_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> StreamingResponse:
    """Server-Sent Events stream tailing the run's Redis Stream (README section 12)."""
    await _get_owned_run(db, generation_id, current_user.id)

    async def event_source() -> AsyncGenerator[str, None]:
        redis = get_redis()
        key = events_stream_key(str(generation_id))
        last_id = "0"
        try:
            while True:
                # Block up to 15s waiting for new entries; emit keep-alive otherwise.
                response = await redis.xread({key: last_id}, block=15000, count=20)
                if not response:
                    yield ": keep-alive\n\n"
                    continue
                for _stream_key, entries in response:
                    for entry_id, fields in entries:
                        last_id = entry_id
                        data = fields.get("data", "{}")
                        yield f"data: {data}\n\n"
                        try:
                            if json.loads(data).get("event") in _TERMINAL:
                                return
                        except json.JSONDecodeError:
                            continue
        finally:
            await redis.aclose()

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
