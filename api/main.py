import time
import uuid
import logging
from fastapi import FastAPI, Request
from core.logging_setup import setup_logging
from core.db import check_connection, engine
from services.api_service import APIService
from services.etl_service import ETLService
from core import models

logger = logging.getLogger("api")
app = FastAPI(title="Kasparro Backend & ETL")

# ensure tables exist at startup
models.Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "service": "kasparro-backend",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "data": "/data",
            "stats": "/stats",
            "docs": "/docs"
        }
    }


@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.time()
    response = await call_next(request)
    latency = int((time.time() - start) * 1000)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Api-Latency-Ms"] = str(latency)
    return response


@app.get("/health")
def health():
    db_ok = check_connection()
    last = ETLService.last_run()
    return {
        "db": db_ok,
        "last_etl": {
            "status": last.status if last else None,
            "run_started_at": str(last.run_started_at) if last else None
        }
    }


@app.get("/data")
def get_data(limit: int = 50, offset: int = 0, q: str | None = None, request: Request = None):
    start = time.time()
    items, total = APIService.list_assets(limit=limit, offset=offset, q=q)
    latency = int((time.time() - start) * 1000)
    return {
        "request_id": request.headers.get("X-Request-Id"),
        "api_latency_ms": latency,
        "limit": limit,
        "offset": offset,
        "total": total,
        "data": [
            {
                "id": a.id,
                "external_id": a.external_id,
                "symbol": a.symbol,
                "name": a.name,
                "source": a.source
            } for a in items
        ]
    }


@app.get("/stats")
def stats():
    return ETLService.stats()
