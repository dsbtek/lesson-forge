"""Generation job orchestration: create rows and enqueue the ARQ task."""

from __future__ import annotations

from arq.connections import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GenerationRun, Lesson, User
from app.schemas.lesson import LessonRequest


async def start_generation(
    db: AsyncSession,
    arq_pool: ArqRedis,
    user: User,
    req: LessonRequest,
) -> tuple[Lesson, GenerationRun]:
    """Create the Lesson + GenerationRun rows and enqueue the worker job.

    The FastAPI request returns immediately; the ARQ worker runs the LangGraph
    pipeline (README section 18: never run long generation in the HTTP request).
    """
    title = req.topic or f"{req.subject} lesson"
    lesson = Lesson(
        user_id=user.id,
        title=title,
        subject=req.subject,
        grade=req.grade,
        duration_minutes=req.duration_minutes,
    )
    db.add(lesson)
    await db.flush()  # assigns lesson.id

    run = GenerationRun(lesson_id=lesson.id, status="queued", revision=0)
    db.add(run)
    await db.flush()  # assigns run.id
    await db.commit()

    await arq_pool.enqueue_job("run_generation", str(run.id), req.model_dump())
    return lesson, run
