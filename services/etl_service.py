import logging
from sqlalchemy import select, desc
from core.db import SessionLocal
from core.models import ETLRun

logger = logging.getLogger("services.etl")

class ETLService:
    @staticmethod
    def last_run():
        with SessionLocal() as session:
            return session.execute(select(ETLRun).order_by(desc(ETLRun.run_started_at)).limit(1)).scalar_one_or_none()

    @staticmethod
    def stats():
        with SessionLocal() as session:
            total = session.query(ETLRun).count()
            last_success = session.execute(select(ETLRun).where(ETLRun.status=="success").order_by(desc(ETLRun.run_finished_at)).limit(1)).scalar_one_or_none()
            last_failure = session.execute(select(ETLRun).where(ETLRun.status=="failed").order_by(desc(ETLRun.run_finished_at)).limit(1)).scalar_one_or_none()
            return {
                "total_runs": total,
                "last_success": last_success.run_finished_at.isoformat() if last_success and last_success.run_finished_at else None,
                "last_failure": last_failure.run_finished_at.isoformat() if last_failure and last_failure.run_finished_at else None,
            }
