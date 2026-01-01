# Kasparro Backend & ETL

A production-grade backend and ETL system for crypto asset data.

## System Architecture

- **FastAPI Core**: A high-performance, non-blocking API layer serving canonical asset data.
- **ETL Ingestion Pipeline**: An idempotent background service that unifies data from CoinGecko, CoinPaprika, and CSV.
- **PostgreSQL Persistence**: A structured database layer using identity unification to map disparate source IDs to single canonical entities.

## Symbol Collision Handling

In crypto data, symbol collisions (e.g., multiple assets named "SOL") are unavoidable.
- **Rationale**: We use `(source, external_id)` as the unique primary identifier.
- **Strategy**: If a symbol is already mapped to a different external ID, the system **intentionally skips** the new record.
- **Idempotency**: This prevents data duplication and corruption while ensuring a stable, predictable state.

## Railway Deployment

- **Port Binding**: The server dynamically binds to `$PORT` (default 8080) and host `0.0.0.0`.
- **Root Endpoint**: `GET /` provides an immediate JSON response for status verification.
- **Health Checks**: `GET /health` monitors database connectivity.
- **Non-Blocking Ingestion**: ETL runs in the background via `POST /etl/run` to avoid application timeout during startup.

## API Endpoints
- `GET /`: Service status
- `GET /health`: Health check
- `POST /etl/run`: Trigger ingestion
- `GET /data`: Paginated assets
- `GET /stats`: ETL metrics
