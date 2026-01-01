# Kasparro – Backend & ETL Systems

## Project Overview
A production-grade backend and ETL system for crypto asset data. The system ingests data from multiple sources (CoinGecko, CoinPaprika APIs, and CSV), normalizes it into a unified canonical schema, and exposes a FastAPI service for querying and observability.

## Architecture
- **api/**: FastAPI routes and middleware.
- **ingestion/**: ETL orchestration and source adapters.
- **services/**: Business logic for API and ETL processes.
- **core/**: Database models, configuration, and logging setup.
- **schemas/**: Pydantic validation schemas.
- **tests/**: Automated test suite.

## Key Features
- **Canonical Normalization**: Unifies assets from different sources by symbol into a single identity.
- **Incremental Ingestion**: Uses checkpoints to resume from the last processed record.
- **Failure Recovery**: Durable checkpointing ensures data integrity even after mid-run failures.
- **Dockerized Environment**: Multi-stage build for optimized production deployment.
- **Observability**: Structured JSON logging and dedicated health/stats endpoints.

## API Endpoints
- `GET /`: Service status metadata.
- `GET /health`: DB connectivity and last ETL run status.
- `GET /stats`: Aggregated ETL run metrics (records, processed records, last success/failure).
- `GET /data`: Paginated asset list with unified source mappings and search.

## Setup and Running

### Prerequisites
- Docker & Docker Compose
- PostgreSQL (if running outside Docker)

### Local Development (Docker)
```bash
docker compose up --build
```
The API will be available at `http://localhost:5000`.

### Running Tests
```bash
export PYTHONPATH=$PYTHONPATH:.
python -m pytest
```

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string.
- `COINPAPRIKA_API_KEY`: API key for CoinPaprika (optional for free tier).
- `COINGECKO_API_KEY`: API key for CoinGecko.
- `ETL_FAIL_AFTER_N_RECORDS`: For testing failure recovery logic.
