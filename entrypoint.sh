#!/bin/sh
set -e

PORT=${PORT:-8000}
echo "Starting FastAPI server on port $PORT"

# Wait a bit for database to be ready (if available)
echo "Waiting for database connection..."
sleep 2

# Run ETL in background (non-blocking) - don't wait for it
echo "Starting ETL process in background..."
python ingestion/run.py || echo "ETL process completed with errors (non-blocking)" &

# Start FastAPI immediately - this is the main process
exec uvicorn api.main:app \
  --host 0.0.0.0 \
  --port $PORT \
  --timeout-keep-alive 30
