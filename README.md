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

### Handling Symbol Collisions

In the fragmented world of crypto data, symbol collisions (e.g., multiple different assets using "SOL" or "WETH") are common. Kasparro is designed with this real-world inconsistency in mind:

- **Canonical Identity**: The system uses `(source, external_id)` as the unique canonical identifier for an asset mapping.
- **Resilience**: When a symbol already exists but maps to a different `external_id` at the same source, the ingestion pipeline intentionally **skips** the new record. 
- **Integrity**: We prioritize data integrity over coverage—no overwriting or duplicating happens automatically. These events are logged as `INFO` with a summary count at the end of each run.

#### Ingestion Flow
1. **Fetch**: Stream assets from provider (CoinGecko/CoinPaprika).
2. **Normalize**: Map symbol to a canonical internal ID.
3. **Validate**: Check if this symbol already exists from this source.
   - If `external_id` matches → Skip (Already ingested).
   - If `external_id` differs → Skip & Log (Collision detected).
   - If new → Insert & Link.
4. **Checkpoint**: Update source cursor for next run.

## Technical Stack
- **Language**: Python 3.11
- **Framework**: FastAPI
- **Database**: PostgreSQL / SQLAlchemy
- **Containerization**: Docker (Multi-stage)
