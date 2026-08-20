#!/usr/bin/env sh
# Entrypoint for the api/worker containers.
# 1. Wait for Postgres to accept connections.
# 2. If RUN_MIGRATIONS=1 (api only), apply Alembic migrations.
# 3. Exec the container command (uvicorn or arq).
set -e

PGHOST="${POSTGRES_HOST:-postgres}"
PGPORT="${POSTGRES_PORT:-5432}"
PGUSER="${POSTGRES_USER:-forge}"

echo "[entrypoint] waiting for postgres at ${PGHOST}:${PGPORT}..."
until pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" >/dev/null 2>&1; do
  sleep 1
done
echo "[entrypoint] postgres is ready."

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "[entrypoint] applying database migrations..."
  alembic upgrade head
  echo "[entrypoint] migrations complete."
fi

echo "[entrypoint] starting: $*"
exec "$@"
