from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from .config import settings
import logging

logger = logging.getLogger("core.db")

# Normalize DATABASE_URL for Railway/cloud deployments
# Railway may provide postgres:// but SQLAlchemy needs postgresql://
def normalize_database_url(url: str) -> str:
    """Normalize database URL for compatibility."""
    if url.startswith("postgres://"):
        # Convert postgres:// to postgresql:// for SQLAlchemy
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+psycopg2" not in url:
        # Ensure psycopg2 driver is specified
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

# Create engine with connection pooling and retry settings for cloud deployments
# pool_pre_ping=True ensures connections are validated before use
db_url = normalize_database_url(settings.DATABASE_URL)
is_postgres = "postgresql" in db_url.lower() or "postgres" in db_url.lower()

connect_args = {}
if is_postgres:
    connect_args = {
        "connect_timeout": 10,
        # Railway/cloud databases often require SSL
        "sslmode": "prefer"  # Try SSL but fallback to non-SSL if needed
    }

engine = create_engine(
    db_url,
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=300,    # Recycle connections after 5 minutes
    connect_args=connect_args,
    echo=False  # Set to True for debugging SQL queries
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_connection():
    """Check database connection with retry logic for cloud deployments."""
    import time
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.debug(f"Database connection attempt {attempt + 1}/{max_retries} failed, retrying...")
                time.sleep(retry_delay)
            else:
                logger.warning(f"Database connection failed after {max_retries} attempts: {str(e)[:100]}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error checking database connection: {e}")
            return False
    return False
