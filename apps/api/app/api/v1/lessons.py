"""Lesson endpoints: generate, read, update, regenerate section, export."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import desc, select

from app.api.deps import ArqPool, CurrentUser, DbSession
from app.core.rate_limit import generation_rate_limit
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
from app.services.export import render_export, save_export_artifact
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
    _rate_limit: generation_rate_limit = None,
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


@router.post(
    "/{lesson_id}/exports", response_model=ExportRead, status_code=status.HTTP_202_ACCEPTED
)
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

    # Render the export artifact into the requested format (Phase 4).
    data, ext, _mime = render_export(version.content, payload.format)
    export_id = uuid.uuid4()
    save_export_artifact(str(export_id), data, ext)

    download_url = f"/api/v1/lessons/{lesson_id}/exports/{export_id}/download"
    export = Export(
        id=export_id,
        lesson_version_id=version.id,
        format=payload.format,
        status="completed",
        storage_url=download_url,
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)
    return export


@router.get("/{lesson_id}/exports/{export_id}/download")
async def download_export(
    lesson_id: uuid.UUID,
    export_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    """Download a rendered export artifact (Phase 4)."""
    await _get_owned_lesson(db, lesson_id, current_user)
    export = await db.get(Export, export_id)
    if export is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")

    version = await db.get(LessonVersion, export.lesson_version_id)
    if version is None or version.lesson_id != lesson_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")

    data, ext, mime_type = render_export(version.content, export.format)
    filename = f"lesson_{lesson_id}_{export.format}.{ext}"

    return Response(
        content=data,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
