#!/usr/bin/env bash
set -e
# start ETL in background, then start API
python -m ingestion.run &
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
