# Kasparro Backend & ETL

A production-grade backend and ETL system for crypto asset data. This system ingests data from multiple providers, normalizes it into a unified canonical schema, and exposes a high-performance FastAPI service for querying.

## System Architecture

The project follows a clean service-oriented architecture:
- **ETL Pipeline**: Idempotent ingestion engine with source-specific adapters (CoinGecko, CoinPaprika, CSV).
- **Database Layer**: PostgreSQL backend using SQLAlchemy ORM for structured data storage and identity unification.
- **API Layer**: FastAPI-driven REST service providing standard endpoints and automated documentation.
- **Normalization Engine**: Logic to unify assets across fragmented data sources into a single "Source of Truth".

## Data Ingestion Design

### Idempotent Ingestion
The pipeline is designed to be fully idempotent. It uses a checkpoint system to resume from the last successful record and ensures that duplicate data is never created, even if the ETL runs multiple times or fails mid-run.

### Handling Identity Collisions
A major challenge in crypto data is symbol collision (e.g., multiple "SOL" or "LTC" tokens). Kasparro addresses this by:
1. Creating a **Canonical Coin** record for a unique symbol.
2. Mapping provider-specific **External IDs** to that canonical coin.
3. Detecting conflicts where a provider attempts to map a symbol to a different ID than already stored. These are logged as warnings and skipped to prevent data corruption.

## Real-World Challenges Addressed

- **Provider Inconsistency**: Different providers use different internal naming conventions. We map these to a single internal identifier.
- **Fault Tolerance**: The system handles API failures, rate limiting, and database disconnects gracefully.
- **Deployment Ready**: Optimized for modern cloud platforms like Railway with multi-stage Docker builds and automated health checks.

## Key Endpoints
- `GET /health` - Service and Database status
- `GET /data` - Paginated canonical coin list with source metadata
- `GET /stats` - ETL pipeline metrics and last run info
- `GET /docs` - Interactive OpenAPI documentation

## Technical Stack
- **Language**: Python 3.11
- **Framework**: FastAPI
- **Database**: PostgreSQL / SQLAlchemy
- **Containerization**: Docker (Multi-stage)
