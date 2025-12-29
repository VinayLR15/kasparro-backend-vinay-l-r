import time
import uuid
import logging
from fastapi import FastAPI, Request
from core.logging_setup import setup_logging
from core.db import check_connection, engine
from core.config import settings
from services.api_service import APIService
from services.etl_service import ETLService
from core import models

logger = logging.getLogger("api")
app = FastAPI(title="Kasparro Backend & ETL")

# ensure tables exist at startup (with retry logic for cloud deployments)
def ensure_tables():
    """Create tables with retry logic for cloud deployments."""
    import time
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            models.Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Failed to create tables (attempt {attempt + 1}/{max_retries}): {e}. Retrying...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to create tables after {max_retries} attempts: {e}")
                # Don't raise - let the app start and handle DB errors gracefully

# Call ensure_tables at startup (non-blocking for health checks)
try:
    ensure_tables()
except Exception as e:
    logger.error(f"Warning: Could not create tables at startup: {e}. App will continue but may have DB issues.")

@app.on_event("startup")
async def startup_event():
    """Log startup for debugging."""
    logger.info("FastAPI application started")
    logger.info(f"Database URL configured: {settings.DATABASE_URL[:20]}..." if len(settings.DATABASE_URL) > 20 else f"Database URL: {settings.DATABASE_URL}")


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
    # Store request_id in request state for use in endpoints
    request.state.request_id = request_id
    start = time.time()
    response = await call_next(request)
    latency = int((time.time() - start) * 1000)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Api-Latency-Ms"] = str(latency)
    return response


@app.get("/health")
def health():
    """Health check endpoint - must work even if DB isn't ready."""
    try:
        db_ok = check_connection()
    except Exception as e:
        logger.warning(f"Health check: DB connection failed: {e}")
        db_ok = False
    
    last = None
    try:
        last = ETLService.last_run()
    except Exception as e:
        logger.warning(f"Health check: Could not get last ETL run: {e}")
    
    return {
        "status": "ok" if db_ok else "degraded",
        "db": db_ok,
        "last_etl": {
            "status": last.status if last else None,
            "run_started_at": str(last.run_started_at) if last else None
        }
    }


@app.get("/data")
def get_data(limit: int = 50, offset: int = 0, q: str | None = None, request: Request = None):
    """
    Get canonical coins with their source mappings.
    Returns unified coins (normalized by symbol) showing all sources for each coin.
    """
    start = time.time()
    items, total = APIService.list_assets(limit=limit, offset=offset, q=q)
    latency = int((time.time() - start) * 1000)
    return {
        "request_id": request.state.request_id if hasattr(request.state, 'request_id') else None,
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
                        "source": cs.source,
                        "external_id": cs.external_id,
                        "source_metadata": cs.source_metadata
                    }
                    for cs in item["sources"]
                ]
            }
            for item in items
        ]
    }


@app.get("/stats")
def stats():
    return ETLService.stats()
