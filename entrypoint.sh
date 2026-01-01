#!/bin/sh
set -e

# Ensure current directory is in PYTHONPATH so "core" module is found
export PYTHONPATH=$PYTHONPATH:.

# Port handling for Railway
PORT=${PORT:-5000}
echo "Starting Kasparro Backend on port $PORT"

# Start API immediately (ETL is now triggered via endpoint or background task)
exec python -m uvicorn api.main:app \
  --host 0.0.0.0 \
  --port $PORT
