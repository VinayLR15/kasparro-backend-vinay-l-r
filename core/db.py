# core/db.py
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

logger = logging.getLogger("core.db")

Base = declarative_base()
_engine = None
_SessionLocal = None


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def get_engine():
    global _engine, _SessionLocal

    if _engine is not None:
        return _engine

    db_url = os.getenv("DATABASE_URL", "").strip()
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    db_url = normalize_database_url(db_url)

    connect_args = {}
    if "postgresql" in db_url:
        connect_args = {
            "connect_timeout": 10,
            "sslmode": "prefer",
        }

    _engine = create_engine(
        db_url,
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args=connect_args,
        echo=False,
    )

    _SessionLocal = sessionmaker(
        bind=_engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    logger.info("Database engine initialized")
    return _engine


def get_session():
    if _SessionLocal is None:
        get_engine()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def SessionLocal():
    if _SessionLocal is None:
        get_engine()
    return _SessionLocal()


engine = get_engine()


def check_connection() -> bool:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
