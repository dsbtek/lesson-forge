"""Aggregate v1 router."""

from fastapi import APIRouter

from app.api.v1 import auth, generations, lessons

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(lessons.router)
api_router.include_router(generations.router)
