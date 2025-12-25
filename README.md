```md
# Kasparro – Backend & ETL Systems Assignment

## Project Overview

This project implements a **production-grade backend and ETL system** as specified in the Kasparro Backend & ETL Systems assignment.

The system ingests crypto asset data from multiple sources (APIs and CSV), stores raw payloads, normalizes data into a unified schema, and exposes a FastAPI service for querying, monitoring, and observability.

The implementation focuses on **robust ETL design**, **incremental ingestion**, **failure recovery**, **clean architecture**, and **cloud-ready deployment**.

---

## Architecture

### API Layer
- **Location**: `api/main.py`
- Built using **FastAPI**
- Routes only; no business logic in controllers
- Exposes health, data, stats, and documentation endpoints

### ETL Layer
- **Location**: `ingestion/run.py`
- Orchestrates ingestion from all data sources
- Writes raw data and normalized assets
- Records ETL runs and checkpoints

### Data Storage
- **raw_assets**: Stores raw source payloads unchanged
- **assets**: Stores normalized, canonical asset records
- **etl_runs**: Tracks ETL execution metadata
- **etl_checkpoints**: Stores per-source incremental progress

### Clean Separation
```

api/          → API routes
ingestion/   → ETL orchestration
services/    → Business logic
schemas/     → Pydantic validation
core/        → DB, config, logging
tests/       → Automated tests

````

---

## ETL Design

### Data Sources
- CoinPaprika API (configured via environment variable)
- CoinGecko API
- CSV file (`ingestion/data/assets.csv`)

### Incremental Ingestion
- Each source maintains a checkpoint (`last_record_id`)
- On restart, ETL resumes after the checkpoint
- Prevents reprocessing of already ingested data

### Idempotent Writes
- Raw records are unique by `(source, record_id)`
- Normalized assets are unique by `(external_id, source)`
- Duplicate inserts are safely ignored

### Unified Schema
- Pydantic models in `schemas/asset.py`
- Ensures consistent normalized asset structure across all sources

---

## P2 Highlight — Failure Injection & Strong Recovery

### Controlled Failure Injection
Configure using environment variable:
```bash
ETL_FAIL_AFTER_N_RECORDS=2
````

* ETL intentionally raises an exception after processing N records
* Simulates partial pipeline failure

### Checkpoint Commit

* Checkpoints are committed **before** failure
* Ensures progress is durable

### Recovery

* Restart ETL without the failure variable
* ETL resumes from the next record
* No partially committed or duplicate data

---

## API Endpoints

### GET /

Returns service metadata and available endpoints

### GET /data

* Pagination with `limit` and `offset`
* Optional `q` search filter
* Returns:

  * `request_id`
  * `api_latency_ms`
  * Paging metadata
  * Asset data array

### GET /health

* Database connectivity status
* Last ETL run summary

### GET /stats

* Aggregated ETL metrics from `etl_runs`
* Records processed
* Success and failure timestamps

### GET /docs

* Swagger API documentation

---

## Live Deployment (Railway)

**Base URL**

```
https://kasparro-backend-vinay-l-r-production.up.railway.app
```

**Quick Checks**

* `/health`
* `/data?limit=5`
* `/docs`

---

## How to Run Locally

### Docker

```bash
docker compose up --build
```

Verify:

```bash
curl http://localhost:8080/health
```

### Tests

```bash
python -m pytest -q
```

Tests use isolated SQLite databases and mocked external sources.

---

## Smoke Test / Live Demo

### Step 1: Start the System

```bash
docker compose up --build
```

Confirm:

```bash
curl http://localhost:8080/health
```

### Step 2: Initial ETL Run

```bash
curl http://localhost:8080/stats
```

Expected:

* `status: "success"`
* Non-zero `records_processed`

### Step 3: Inject Controlled Failure

```bash
docker compose down
ETL_FAIL_AFTER_N_RECORDS=2 docker compose up --build
```

Expected:

* ETL fails after 2 records
* Failure recorded in `etl_runs`

### Step 4: Recovery Run

```bash
docker compose down
unset ETL_FAIL_AFTER_N_RECORDS
docker compose up --build
```

Expected:

* ETL resumes from checkpoint
* No duplicate records
* Successful run recorded

### Step 5: API Validation

```bash
curl "http://localhost:8080/data?limit=5"
curl http://localhost:8080/health
curl http://localhost:8080/stats
```

---

## Cloud Deployment Notes

* Fully Dockerized and cloud-ready
* Compatible with AWS, GCP, and Azure
* Database configurable via `DATABASE_URL`
* Logs emitted as structured JSON to stdout
* ETL can be scheduled using cron or cloud schedulers

---

## Configuration

Environment variables:

* `DATABASE_URL`
* `COINPAPRIKA_API_KEY`
* `ETL_FAIL_AFTER_N_RECORDS` (optional)

No secrets are hardcoded in the repository.

---

## Repository

GitHub:

```
https://github.com/VinayLR15/kasparro-backend-vinay-l-r
```

---

## Submission Checklist

* [x] Docker runs locally without errors
* [x] All tests passing
* [x] ETL recovery verified
* [x] No secrets committed
* [x] Public cloud deployment working

---

## Status

**Assignment complete, deployed, and production-ready.**

```
```
