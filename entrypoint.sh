#!/bin/sh
set -e

# Ensure current directory is in PYTHONPATH so "core" module is found
export PYTHONPATH=$PYTHONPATH:.

PORT=${PORT:-5000}
echo "Starting Kasparro Backend on port $PORT"

# Run ingestion
python ingestion/run.py

# Start API
exec python -m uvicorn api.main:app \
  --host 0.0.0.0 \
  --port $PORT
