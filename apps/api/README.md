# LessonForge API

FastAPI + LangGraph service for agentic lesson-plan generation.

See the root [README.md](../../README.md) for the full architecture. This package is the
**Phase 1 foundation**: schemas, models, migrations, JWT auth, an ARQ worker, and a stubbed
LangGraph pipeline. Agent intelligence, RAG, and real exports are later phases (marked `# TODO`).

## Layout

```
app/
  main.py            # app factory, health, /metrics
  config.py          # settings
  db/                # async engine + declarative base
  core/security.py   # password hashing + JWT
  models/            # SQLAlchemy models (README ERD + knowledge chunks)
  schemas/           # Pydantic request/response + LangGraph state
  api/v1/            # auth, lessons, generations routers
  services/          # redis client, generation job orchestration
  graph/             # LangGraph StateGraph (stub nodes)
  agents/            # per-agent stubs
  workers/           # ARQ worker
alembic/             # migrations
tests/               # DB-independent unit tests
```

## Local (via Docker)

```
docker compose up --build      # from repo root
```
