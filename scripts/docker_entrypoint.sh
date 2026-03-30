#!/usr/bin/env bash
set -e

# Wait for Postgres to be available and run alembic migrations, then start uvicorn
DB_URL=${DATABASE_URL:-${DB_URL:-}}
if [ -n "$DB_URL" ]; then
  echo "Waiting for database..."
  # crude wait loop
  for i in {1..30}; do
    if python - <<PYCODE
import sys
import os
from urllib.parse import urlparse
import psycopg2
url = os.getenv('DATABASE_URL') or os.getenv('DB_URL')
if not url:
    sys.exit(1)
try:
    p = urlparse(url)
    conn = psycopg2.connect(dbname=p.path.lstrip('/'), user=p.username, password=p.password, host=p.hostname, port=p.port, connect_timeout=2)
    conn.close()
    sys.exit(0)
except Exception:
    sys.exit(2)
PYCODE
    then
      echo "Database is up"
      break
    fi
    echo "Waiting... ($i)"
    sleep 2
  done
  echo "Running alembic upgrade head"
  alembic upgrade head || true
fi

echo "Starting uvicorn"
exec uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers
