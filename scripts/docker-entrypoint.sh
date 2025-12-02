#!/usr/bin/env bash
set -euo pipefail

echo "Applying database migrations..."
alembic upgrade head

echo "Seeding demo user..."
python scripts/seed_demo_user.py || true

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
