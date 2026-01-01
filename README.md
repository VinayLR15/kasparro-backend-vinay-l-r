# Kasparro Backend & ETL

Production-grade crypto data ingestion and API service.

## Architecture
- **API (FastAPI)**: Non-blocking web server with automated health checks and documentation.
- **ETL (Background Processing)**: Idempotent ingestion pipeline that processes data from CoinPaprika, CoinGecko, and CSV without blocking the main thread.
- **Persistence (PostgreSQL)**: Unified schema mapping multiple data sources to canonical coin entities.

## Ingestion Strategy & Reliability

### Non-Blocking Startup
To ensure 100% availability on Railway, the web server starts immediately. Data ingestion is triggered via the `/etl/run` endpoint as a background task, preventing "Application failed to respond" timeouts.

### Symbol Collision Handling
Symbol collisions are expected in crypto data. The system uses a strict idempotent strategy:
1. Assets are uniquely identified by `(source, external_id)`.
2. If a new asset shares a symbol with an existing one but has a different `external_id`, it is logged as a `WARNING` and skipped.
3. This prevents data corruption while ensuring the pipeline remains stable.

## API Usage
- `GET /`: Service status
- `GET /health`: Detailed system health
- `POST /etl/run`: Trigger ingestion pipeline
- `GET /data`: Paginated asset querying
- `GET /docs`: Interactive Swagger UI

## Railway Deployment
- The app binds to `0.0.0.0` on the port provided by the environment variable `$PORT`.
- Ensure `DATABASE_URL` is configured in service variables.
