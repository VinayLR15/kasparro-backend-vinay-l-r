#!/bin/sh
set -e

echo "Starting ETL process..."
python ingestion/run.py || true

echo "Starting FastAPI server..."
exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
