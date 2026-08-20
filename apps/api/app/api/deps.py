"""Shared FastAPI dependencies: DB session, current user, ARQ pool."""

from __future__ import annotations

import uuid
from typing import Annotated

import jwt
from arq.connections import ArqRedis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import decode_token
from app.db.session import get_session
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exc
        user_id = uuid.UUID(subject)
    except (jwt.PyJWTError, ValueError) as exc:
        raise credentials_exc from exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_arq(request: Request) -> ArqRedis:
    """Return the ARQ pool created during app startup."""
    pool: ArqRedis | None = getattr(request.app.state, "arq_pool", None)
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job queue is not available",
        )
    return pool


ArqPool = Annotated[ArqRedis, Depends(get_arq)]
