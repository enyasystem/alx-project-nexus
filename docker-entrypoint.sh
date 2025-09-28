#!/bin/sh
set -e

# If pg_isready is available and POSTGRES_HOST is set, wait for DB
if command -v pg_isready >/dev/null 2>&1 && [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for Postgres at ${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}..."
  until pg_isready -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-postgres}"; do
    sleep 1
  done
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Ensuring admin user exists (if ADMIN_* env vars provided)..."
python -m scripts.create_admin_if_missing || true

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Exec the container CMD
exec "$@"
