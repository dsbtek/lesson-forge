# LessonForge Web (Next.js)

Phase 1 scaffold: Next.js 14 (App Router) + TypeScript + Tailwind.

A single page (`app/page.tsx`) renders:

- **HealthBadge** — polls the API `GET /health` and shows online/offline.
- **LessonForm** — the README example lesson request (grade, subject, topic,
  duration, standards, strategy, learner profiles, assessment type). On submit it
  registers + logs in a demo account, then `POST`s to
  `/api/v1/lessons/generate` and shows the returned `generation_id` / `lesson_id`.

The API base URL comes from `NEXT_PUBLIC_API_URL` (see `lib/api.ts`).

## Phase 4 (not built yet)

Live SSE progress streaming, the lesson editor, versioning UI, exports UI, and a
real auth/session flow. A production multi-stage Docker build (`next build`/`start`)
also replaces the dev-mode container.

## Local dev (outside Docker)

```bash
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Or via the repo root: `docker compose up web`.
