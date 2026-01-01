# Kasparro Backend & ETL

## Overview
A production-grade backend and ETL system for crypto asset data. Ingests data from multiple sources (CoinGecko, CoinPaprika APIs and CSV), normalizes it into a unified schema, and exposes a FastAPI service for querying.

## Architecture
- **api/** - FastAPI routes (main.py)
- **core/** - Database, config, logging, models
- **services/** - Business logic (APIService, ETLService)
- **schemas/** - Pydantic validation
- **ingestion/** - ETL orchestration and data sources
- **tests/** - Automated tests

## Key Endpoints
- `GET /` - Service status
- `GET /health` - Health check
- `GET /data` - List coins with pagination and search
- `GET /stats` - ETL run statistics
- `GET /docs` - Swagger API documentation

## Running
The FastAPI server runs on port 5000 with uvicorn.

## Database
Uses PostgreSQL via DATABASE_URL environment variable.

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string (auto-configured)
- `COINPAPRIKA_API_KEY` - Optional API key for CoinPaprika
- `ETL_FAIL_AFTER_N_RECORDS` - Optional, for testing failure recovery
