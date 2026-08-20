"""Lesson endpoints: generate, read, update, regenerate section, export."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import desc, select

from app.api.deps import ArqPool, CurrentUser, DbSession
from app.models import Export, Lesson, LessonVersion, User
from app.schemas.lesson import (
    ExportRead,
    ExportRequest,
    GenerateResponse,
    LessonRead,
    LessonRequest,
    LessonUpdate,
    LessonVersionRead,
)
from app.services.generation import start_generation

router = APIRouter(prefix="/lessons", tags=["lessons"])


async def _get_owned_lesson(db: DbSession, lesson_id: uuid.UUID, user: User) -> Lesson:
    lesson = await db.get(Lesson, lesson_id)
    if lesson is None or lesson.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_lesson(
    req: LessonRequest,
    db: DbSession,
    arq: ArqPool,
    current_user: CurrentUser,
) -> GenerateResponse:
    lesson, run = await start_generation(db, arq, current_user, req)
    return GenerateResponse(generation_id=run.id, lesson_id=lesson.id, status=run.status)


@router.get("", response_model=list[LessonRead])
async def list_lessons(db: DbSession, current_user: CurrentUser) -> list[Lesson]:
    result = await db.scalars(
        select(Lesson).where(Lesson.user_id == current_user.id).order_by(desc(Lesson.created_at))
    )
    return list(result)


@router.get("/{lesson_id}", response_model=LessonRead)
async def get_lesson(lesson_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> Lesson:
    return await _get_owned_lesson(db, lesson_id, current_user)


@router.get("/{lesson_id}/versions", response_model=list[LessonVersionRead])
async def list_versions(
    lesson_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> list[LessonVersion]:
    await _get_owned_lesson(db, lesson_id, current_user)
    result = await db.scalars(
        select(LessonVersion)
        .where(LessonVersion.lesson_id == lesson_id)
        .order_by(desc(LessonVersion.version))
    )
    return list(result)


@router.patch("/{lesson_id}", response_model=LessonRead)
async def update_lesson(
    lesson_id: uuid.UUID,
    payload: LessonUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Lesson:
    lesson = await _get_owned_lesson(db, lesson_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lesson, field, value)
    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.post(
    "/{lesson_id}/sections/{section_id}/regenerate",
    response_model=GenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def regenerate_section(
    lesson_id: uuid.UUID,
    section_id: str,
    db: DbSession,
    arq: ArqPool,
    current_user: CurrentUser,
) -> GenerateResponse:
    # TODO(phase4): resume the graph from the affected node instead of a full re-run.
    lesson = await _get_owned_lesson(db, lesson_id, current_user)
    req = LessonRequest(
        grade=lesson.grade or "",
        subject=lesson.subject or "",
        topic=lesson.title,
        duration_minutes=lesson.duration_minutes or 60,
    )
    _, run = await start_generation(db, arq, current_user, req)
    return GenerateResponse(generation_id=run.id, lesson_id=lesson.id, status=run.status)


@router.post("/{lesson_id}/exports", response_model=ExportRead, status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    lesson_id: uuid.UUID,
    payload: ExportRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> Export:
    await _get_owned_lesson(db, lesson_id, current_user)

    if payload.version_id is not None:
        version = await db.get(LessonVersion, payload.version_id)
    else:
        version = await db.scalar(
            select(LessonVersion)
            .where(LessonVersion.lesson_id == lesson_id)
            .order_by(desc(LessonVersion.version))
            .limit(1)
        )
    if version is None or version.lesson_id != lesson_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No lesson version available to export",
        )

    # TODO(phase4): render the artifact (DOCX/PDF) and upload to object storage.
    export = Export(lesson_version_id=version.id, format=payload.format, status="pending")
    db.add(export)
    await db.commit()
    await db.refresh(export)
    return export
