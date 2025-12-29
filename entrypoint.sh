#!/bin/sh
set -e

echo "Starting ETL process..."
python ingestion/run.py || echo "ETL process completed with errors (non-blocking)"

PORT=${PORT:-8000}
echo "Starting FastAPI server on port $PORT"

exec uvicorn api.main:app \
  --host 0.0.0.0 \
  --port $PORT \
  --timeout-keep-alive 30
