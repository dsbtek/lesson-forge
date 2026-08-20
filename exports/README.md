# exports/

Local scratch directory for rendered lesson exports (DOCX / PDF / Markdown) during
development. In Docker/production, export artifacts are stored in MinIO/S3 and
referenced by `Export.storage_url`; this directory is a dev-only fallback.

Real export rendering is Phase 4 — today `POST /api/v1/lessons/{id}/exports`
records a `pending` Export row without producing a file.
