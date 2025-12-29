import time
import uuid
import logging
import threading

from fastapi import FastAPI, Request
from sqlalchemy import text

from core.logging_setup import setup_logging
from core.db import check_connection, engine
from core.config import settings
from core import models
from services.api_service import APIService
from services.etl_service import ETLService

# --------------------------------------------------
# Logging setup
# --------------------------------------------------
setup_logging()
logger = logging.getLogger("api")

# --------------------------------------------------
# FastAPI app
# --------------------------------------------------
app = FastAPI(title="Kasparro Backend & ETL")


# --------------------------------------------------
# Database initialization with retry (non-blocking)
# --------------------------------------------------
def ensure_tables():
    """
    Create database tables with retry logic.
    Runs in background so app can start even if DB is not ready.
    """
    max_retries = 10
    retry_delay = 3

    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            models.Base.metadata.create_all(bind=engine)
            logger.info("Database tables ensured successfully")
            return
        except Exception as e:
            if attempt < max_retries:
                logger.info(
                    f"Database not ready (attempt {attempt}/{max_retries}), retrying..."
                )
                time.sleep(retry_delay)
            else:
                logger.warning(
                    "Database not available after retries. "
                    "Application will continue without DB-dependent features."
                )


def init_tables_background():
    try:
        ensure_tables()
    except Exception as e:
        logger.error(f"Background DB init failed: {e}")


# Start DB init in background thread
threading.Thread(target=init_tables_background, daemon=True).start()


# --------------------------------------------------
# Startup event
# --------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("Kasparro Backend service started")
    logger.info("Waiting for database readiness in background")


# --------------------------------------------------
# Middleware: request ID & latency
# --------------------------------------------------
@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start = time.time()
    response = await call_next(request)
    latency = int((time.time() - start) * 1000)

    response.headers["X-Request-Id"] = request_id
    response.headers["X-Api-Latency-Ms"] = str(latency)
    return response


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------
@app.get("/")
def root():
    return {
        "service": "kasparro-backend",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "data": "/data",
            "stats": "/stats",
            "docs": "/docs",
        },
    }


# --------------------------------------------------
# Healthcheck (CRITICAL: must always return HTTP 200)
# --------------------------------------------------
@app.get("/health")
def health():
    """
    Liveness probe for Railway / cloud platforms.
    Must NOT depend on database or ETL state.
    """
    return {
        "status": "ok",
        "service": "kasparro-backend",
    }


# --------------------------------------------------
# Data API
# --------------------------------------------------
@app.get("/data")
def get_data(
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    request: Request | None = None,
):
    start = time.time()

    try:
        items, total = APIService.list_assets(limit=limit, offset=offset, q=q)
        latency = int((time.time() - start) * 1000)

        return {
            "request_id": request.state.request_id if request else None,
            "api_latency_ms": latency,
            "limit": limit,
            "offset": offset,
            "total": total,
            "data": [
                {
                    "id": item["coin"].id,
                    "symbol": item["coin"].symbol,
                    "name": item["coin"].name,
                    "sources": [
                        {
                            "source": src.source,
                            "external_id": src.external_id,
                            "source_metadata": src.source_metadata,
                        }
                        for src in item["sources"]
                    ],
                }
                for item in items
            ],
        }

    except Exception as e:
        logger.exception("Error in /data endpoint")
        latency = int((time.time() - start) * 1000)

        return {
            "request_id": request.state.request_id if request else None,
            "api_latency_ms": latency,
            "error": "Database connection unavailable. Please ensure database is configured and running.",
            "limit": limit,
            "offset": offset,
            "total": 0,
            "data": [],
        }


# --------------------------------------------------
# Stats API
# --------------------------------------------------
@app.get("/stats")
def stats():
    try:
        return ETLService.stats()
    except Exception:
        logger.exception("Error in /stats endpoint")
        return {
            "error": "Database connection unavailable. Please ensure database is configured and running.",
            "total_runs": 0,
            "total_records_processed": 0,
            "last_success": {
                "timestamp": None,
                "records_processed": None,
                "duration_seconds": None,
            },
            "last_failure": {
                "timestamp": None,
                "error": None,
            },
        }
