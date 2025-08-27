#!/usr/bin/env bash
set -e

if [ -n "${WAIT_FOR_DB}" ]; then
  echo "Waiting for database at ${WAIT_FOR_DB}..."
  python - <<'PY'
import socket, time, os
host, port = os.environ["WAIT_FOR_DB"].split(":")
port = int(port)
for _ in range(120):
    s = socket.socket()
    try:
        s.settimeout(1)
        s.connect((host, port))
        s.close()
        print("DB is up")
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("Database not reachable")
PY
fi

PRIV="/app/app/certs/jwt-private.pem"
PUB="/app/app/certs/jwt-public.pem"
if [ ! -f "$PRIV" ] || [ ! -f "$PUB" ]; then
  echo "Generating JWT key pair..."
  mkdir -p /app/app/certs
  openssl genrsa -out "$PRIV" 2048 >/dev/null 2>&1
  openssl rsa -in "$PRIV" -pubout -out "$PUB" >/dev/null 2>&1
  chmod 600 "$PRIV" "$PUB"
fi

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Uvicorn..."
exec uvicorn app.main:main_app --host "${UVICORN_HOST:-0.0.0.0}" --port "${UVICORN_PORT:-8000}"
