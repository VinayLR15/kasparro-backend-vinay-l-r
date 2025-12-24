Kasparro - Backend & ETL Systems

**Project Overview**
- **What**: A production-grade backend and ETL system that ingests crypto asset data (APIs + CSV), stores raw payloads, normalizes assets, and exposes a FastAPI for querying and observability.
- **Why production-grade**: transactional checkpoints, idempotent writes, structured JSON logging, Docker-ready deployment, isolated tests, and controlled failure-injection with deterministic recovery.

**Architecture**
- **API layer**: [api/main.py](api/main.py) — FastAPI routes only; business logic lives in [services/](services).
- **ETL ingestion layer**: [ingestion/run.py](ingestion/run.py) orchestrates per-source ingestion, writes into 
aw_assets and normalized ssets, and records runs in etl_runs.
- **Raw vs Normalized**: raw payloads persist unchanged in 
aw_assets; canonical data is stored in ssets for downstream use.
- **Checkpointing & recovery**: per-source checkpoint in etl_checkpoints stores last_record_id. Checkpoints are committed before any injected failure so reruns resume safely from last committed point.

**ETL Design**
- **Sources**: CoinPaprika (COINPAPRIKA_API_KEY), CoinGecko, and CSV ([ingestion/data/assets.csv](ingestion/data/assets.csv)).
- **Incremental ingestion**: Streams are processed until an item matching the checkpoint is observed; ingestion resumes after that point to avoid reprocessing.
- **Idempotent writes**: Unique constraints and existence checks prevent duplicates; ETL writes raw records idempotently and uses upsert-like semantics for ssets.
- **Unified schema**: Pydantic validation via schemas in [schemas/asset.py](schemas/asset.py) ensures normalized records conform to Asset model.

**P2 Highlight — Failure Injection & Strong Recovery**
- **How it works**: Set env ETL_FAIL_AFTER_N_RECORDS to an integer. When configured, the ETL will intentionally raise an exception after N processed records to simulate partial failure.
- **Checkpoint commit**: Checkpoints (etl_checkpoints) are updated and committed before the injected failure is raised so progress is durable.
- **Recovery**: Re-running the ETL reads the checkpoint and resumes from the next record; session/transactional handling ensures no partially committed duplicates.
- **Duplicate avoidance**: Raw records have a unique index (source+record_id); normalized assets use a uniqueness constraint on (external_id, source) preventing duplicates across retries.

**API Endpoints**
- **GET /data**: pagination + optional q filter. Returns 
equest_id, pi_latency_ms, paging metadata, and data array.
- **GET /health**: DB connectivity and last ETL run status summary. Implementation: [api/main.py](api/main.py).
- **GET /stats**: aggregated ETL stats (records processed, last success/failure timestamps) from etl_runs.

**How to Run Locally**
- Build & run (Docker): make up (uses docker-compose.yml with Postgres + app).
- Teardown: make down.
- Run tests: make test or pytest (tests use isolated SQLite DB via conftest.py).
- Windows note: use Git Bash or PowerShell with proper environment handling; tests are designed to run on Windows (temporary DB files handled).

**Testing Strategy**
- **Coverage**: ETL transformations, incremental ingestion, failure injection + recovery, idempotent writes, schema mismatch handling, and API endpoints.
- **Isolation**: Tests use per-test SQLite instances and monkeypatching of external sources to ensure determinism ([tests/](tests)).
- **Recovery tests**: 	ests/test_etl.py simulates an injected failure, asserts checkpoint state and failed run(s), then reruns ETL to verify resume and idempotency.

**Smoke Test / Live Demo**

Complete end-to-end verification in under 5 minutes. Follow these steps to validate the system and P2.2 failure injection + recovery.

**Step 1: Start the System**

```bash
docker compose up --build
```

Confirm the API is reachable:
```bash
curl http://localhost:8000/health
```

Expected: HTTP 200 with health status JSON.

---

**Step 2: Initial ETL Run (Successful)**

Watch the ETL ingestion logs during container startup (logs show structured JSON with source, records_processed, status).

Query the health endpoint:
```bash
curl http://localhost:8000/health
```

Query stats for ETL run summary:
```bash
curl http://localhost:8000/stats
```

Expected: `status: "success"`, non-zero `records_processed`, `last_run_timestamp`.

---

**Step 3: Inject Controlled Failure (P2.2 Demo)**

Stop the running container:
```bash
docker compose down
```

Set the failure injection environment variable and restart:
```bash
export ETL_FAIL_AFTER_N_RECORDS=2
docker compose up --build
```

Watch logs — ETL will process 2 records then raise an exception. Logs show failure and checkpoint state (JSON structured logs).

Query stats to confirm failed run:
```bash
curl http://localhost:8000/stats
```

Expected: `status: "failed"`, `records_processed: 2`, failed run timestamp recorded in `etl_runs`.

---

**Step 4: Recovery Run (Resume from Checkpoint)**

Remove the failure injection and restart:
```bash
docker compose down
unset ETL_FAIL_AFTER_N_RECORDS
docker compose up --build
```

Watch logs — ETL reads checkpoint and resumes from record 3 onward (logs show "Resuming from checkpoint").

Query stats:
```bash
curl http://localhost:8000/stats
```

Expected: `status: "success"`, `records_processed > 2` (continued from checkpoint), no duplicate records in `assets` table (verify via DB).

---

**Step 5: API Validation**

Test data endpoint with pagination:
```bash
curl "http://localhost:8000/data?limit=5&offset=0"
```

Expected: `request_id`, `api_latency_ms`, `paging` metadata, and `data` array with up to 5 assets.

Test health endpoint:
```bash
curl http://localhost:8000/health
```

Expected: HTTP 200, DB connected, last ETL run summary.

Test stats endpoint:
```bash
curl http://localhost:8000/stats
```

Expected: Aggregated ETL run metrics (total records, success/failure counts, timestamps).

---

**Step 6: Test Verification**

Run the full test suite locally (tests use isolated SQLite DB, no external dependencies):
```bash
python -m pytest -q
```

Expected: All tests pass (e.g., `4 passed, 21 warnings in 1.73s`).

Tests cover:
- ETL transformations and incremental ingestion
- Failure injection + recovery (P2.2)
- Idempotent writes (no duplicates after retry)
- API endpoints and schema validation

**Cloud Deployment Notes**

This service is production-ready for cloud deployment with minimal configuration changes.

**Compute Platforms:**
- **AWS**: Deploy via ECS (Fargate) with Postgres RDS, or EC2 with managed PostgreSQL.
- **GCP**: Use Cloud Run for the API (stateless, scales automatically) and Cloud SQL for PostgreSQL.
- **Azure**: Deploy via Container Instances or Azure App Service with managed PostgreSQL database.

**ETL Scheduling:**
- **AWS**: Use EventBridge (CloudWatch Events) to trigger ETL via Lambda or directly call the ingestion endpoint.
- **GCP**: Use Cloud Scheduler to invoke the ETL endpoint on a fixed schedule.
- **Azure**: Use Azure Logic Apps or Scheduled Compute Tasks to trigger the ingestion.
- **On-Prem**: Use cron jobs (e.g., `0 */6 * * * python -m ingestion.run`) for periodic runs.

**Logs & Metrics:**
- Logs are emitted as structured JSON to stdout; pipe them to:
	- AWS CloudWatch (ECS automatically forwards logs).
	- GCP Cloud Logging (Cloud Run automatically integrates).
	- Azure Monitor / Application Insights (configure output integration).
- Metrics: Query `/stats` endpoint for ETL run counts, success/failure rates, and processing latency.

**Database Migration:**
- Update `DATABASE_URL` environment variable to point to your cloud Postgres instance.
- Run migrations on first deployment (tables are auto-created on app startup via SQLAlchemy).


**Notes**
- Pydantic v2 prints deprecation warnings for some Field(..., env=...) usage; these are non-blocking.
- DATABASE_URL is the single configuration entry to swap DBs for cloud deployments (Postgres on AWS/GCP/Azure).
- Logs are emitted as structured JSON to stdout for cloud ingestion (CloudWatch, Stackdriver, etc.).

For implementation details, see [ingestion/run.py](ingestion/run.py), [core/models.py](core/models.py), and [tests/test_etl.py](tests/test_etl.py).

---

**Submission Checklist**

Before submitting to evaluators, verify:

- [ ] Docker runs locally: `docker compose up --build` starts without errors.
- [ ] Tests passing: `python -m pytest -q` returns all tests passing (e.g., `4 passed`).
- [ ] No secrets committed: `COINPAPRIKA_API_KEY` not hardcoded; use `.env` or environment variables.
- [ ] API endpoints verified: `curl http://localhost:8000/health` and `curl http://localhost:8000/data` return expected responses.
- [ ] ETL recovery verified: Run with `ETL_FAIL_AFTER_N_RECORDS=2`, confirm failure, then remove env var and confirm recovery with no duplicates.

For deployment validation, follow the **Smoke Test / Live Demo** section above.
