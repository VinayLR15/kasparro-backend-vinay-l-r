#!/bin/sh
set -e

PORT=${PORT:-8080}
echo "Starting Kasparro Backend on port $PORT"

exec python -m uvicorn api.main:app \
  --host 0.0.0.0 \
  --port $PORT
