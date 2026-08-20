# LessonForge API image — shared by the `api` and `worker` services.
# Uses uv for fast, reproducible dependency installation.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    # Keep the virtualenv OUTSIDE /app so the compose bind-mount
    # (./apps/api -> /app) does not hide the installed packages.
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Runtime deps: postgresql-client provides pg_isready for the entrypoint.
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client curl \
    && rm -rf /var/lib/apt/lists/*

# uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first for better layer caching.
COPY apps/api/pyproject.toml ./
COPY apps/api/uv.lock* ./
RUN uv sync --no-install-project

# Application source (overlaid by a bind-mount in dev compose).
COPY apps/api/ ./

COPY infra/docker/api-entrypoint.sh /usr/local/bin/api-entrypoint.sh
RUN chmod +x /usr/local/bin/api-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["api-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
