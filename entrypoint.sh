#!/bin/sh
set -e

PORT=${PORT:-8000}
echo "Starting Kasparro Backend on port $PORT"

# Start FastAPI immediately (REQUIRED for Railway healthcheck)
exec uvicorn api.main:app \
  --host 0.0.0.0 \
  --port $PORT \
  --proxy-headers \
  --timeout-keep-alive 30
