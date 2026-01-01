#!/bin/sh
set -e

PORT=${PORT:-5000}
echo "Starting Kasparro Backend on port $PORT"

python ingestion/run.py

exec python -m uvicorn api.main:app \
  --host 0.0.0.0 \
  --port $PORT
