#!/bin/sh
set -e

# Run Alembic migrations when PostgreSQL is enabled
if [ "${USE_DATABASE}" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
    echo "Migrations complete."
fi

# Railway injects PORT; default to 8000 for local/Docker Compose
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
