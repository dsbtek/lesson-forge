"""Application settings, loaded from environment variables.

Every field has a development-friendly default so the app (and its tests) can be
imported without a populated ``.env``. Real deployments must override secrets.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── App ───────────────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    # Stored as a raw string; use `cors_origins_list` for the parsed value.
    cors_origins: str = "http://localhost:3000"

    # ── Database ──────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://forge:forge@postgres:5432/lessonforge"

    # ── Redis ─────────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"

    # ── Object storage (MinIO / S3) ───────────────────────
    s3_endpoint_url: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "lesson-forge"
    s3_region: str = "us-east-1"

    # ── Auth ──────────────────────────────────────────────
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # ── LLM providers (unused until agents are implemented) ─
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    embedding_dim: int = 1536

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
