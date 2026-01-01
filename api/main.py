# api/main.py
import time
import uuid
import logging
import threading
from fastapi import FastAPI, Request
from sqlalchemy import text

from core.logging_setup import setup_logging
from core.db import get_engine, check_connection
from core import models
from services.api_service import APIService
from services.etl_service import ETLService

setup_logging()
logger = logging.getLogger("api")

app = FastAPI(title="Kasparro Backend & ETL")


# ---------------------------
# Background DB init (SAFE)
# ---------------------------
def ensure_tables():
    retries = 10
    delay = 3

    for attempt in range(1, retries + 1):
        try:
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            models.Base.metadata.create_all(bind=engine)
            logger.info("Database tables created")
            return
        except Exception as e:
            if attempt < retries:
                logger.info(f"DB not ready ({attempt}/{retries}), retrying...")
                time.sleep(delay)
            else:
                logger.warning("DB unavailable, continuing without DB")


threading.Thread(target=ensure_tables, daemon=True).start()


@app.on_event("startup")
async def startup():
    logger.info("Kasparro Backend started")


# ---------------------------
# Middleware
# ---------------------------
@app.middleware("http")
async def request_meta(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.time()
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Api-Latency-Ms"] = str(int((time.time() - start) * 1000))
    return response


# ---------------------------
# Routes
# ---------------------------
@app.get("/")
def root():
    return {"service": "kasparro-backend", "status": "running"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "db": check_connection(),
        "last_etl": ETLService.last_run()
    }


@app.get("/data")
def data(limit: int = 50, offset: int = 0, q: str | None = None, request: Request = None):
    start = time.time()
    try:
        items, total = APIService.list_assets(limit, offset, q)
        return {
            "request_id": request.state.request_id if request else None,
            "latency_ms": int((time.time() - start) * 1000),
            "total": total,
            "data": items,
        }
    except Exception:
        logger.exception("/data failed")
        return {
            "request_id": request.state.request_id if request else None,
            "error": "Database unavailable",
            "data": [],
        }


@app.get("/stats")
def stats():
    try:
        return ETLService.stats()
    except Exception:
        logger.exception("/stats failed")
        return {
            "total_runs": 0,
            "total_records_processed": 0,
        }
