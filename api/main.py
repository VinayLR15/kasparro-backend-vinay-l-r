import os
import time
import uuid
import logging
import threading
from fastapi import FastAPI, Request, BackgroundTasks
from sqlalchemy import text

from core.logging_setup import setup_logging
from core.db import get_engine, check_connection
from core import models
from services.api_service import APIService
from services.etl_service import ETLService
from ingestion.run import run_all

setup_logging()
logger = logging.getLogger("api")

app = FastAPI(title="Kasparro Backend & ETL")

@app.on_event("startup")
async def startup():
    logger.info("Kasparro Backend started")

@app.get("/", status_code=200)
def root():
    return {
        "service": "Kasparro Backend & ETL",
        "status": "ok",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "data": "/data",
            "stats": "/stats",
            "etl_run": "/etl/run (POST)"
        }
    }

@app.head("/")
def root_head():
    return

@app.get("/info")
def info():
    return {
        "service": "Kasparro Backend",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "data": "/data",
            "stats": "/stats",
            "etl_run": "/etl/run (POST)"
        }
    }

@app.get("/health")
def health():
    db_status = check_connection()
    return {
        "status": "ok" if db_status else "error",
        "db": db_status,
        "last_etl": ETLService.last_run()
    }

@app.post("/etl/run")
def trigger_etl(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_all)
    return {"status": "accepted", "message": "ETL run started in background"}

@app.get("/data")
def data(limit: int = 50, offset: int = 0, q: str | None = None, request: Request = None):
    start = time.time()
    try:
        items, total = APIService.list_assets(limit, offset, q)
        return {
            "latency_ms": int((time.time() - start) * 1000),
            "total": total,
            "data": items,
        }
    except Exception:
        logger.exception("/data failed")
        return {
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

if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment variable (standard for Railway)
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
