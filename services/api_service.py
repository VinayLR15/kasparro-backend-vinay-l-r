import logging
from core.db import SessionLocal
from core.models import Asset
from sqlalchemy import select

logger = logging.getLogger("services.api")

class APIService:
    @staticmethod
    def list_assets(limit: int = 50, offset: int = 0, q: str | None = None):
        with SessionLocal() as session:
            stmt = select(Asset)
            if q:
                stmt = stmt.where(Asset.symbol.ilike(f"%{q}%") | Asset.name.ilike(f"%{q}%"))
            stmt = stmt.limit(limit).offset(offset)
            res = session.execute(stmt).scalars().all()
            total = session.query(Asset).count()
            return res, total
