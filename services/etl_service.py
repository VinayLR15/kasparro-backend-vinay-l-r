import logging
from sqlalchemy import select, desc, func as sql_func
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
            total = session.execute(select(sql_func.count(ETLRun.id))).scalar()
            last_success = session.execute(select(ETLRun).where(ETLRun.status=="success").order_by(desc(ETLRun.run_finished_at)).limit(1)).scalar_one_or_none()
            last_failure = session.execute(select(ETLRun).where(ETLRun.status=="failed").order_by(desc(ETLRun.run_finished_at)).limit(1)).scalar_one_or_none()
            
            # Calculate total records processed across all successful runs
            total_records = 0
            if last_success:
                total_records_stmt = session.execute(
                    select(sql_func.sum(ETLRun.records_processed)).where(ETLRun.status == "success")
                ).scalar()
                total_records = total_records_stmt or 0
            
            # Calculate duration for last success if available
            duration_seconds = None
            if last_success and last_success.run_finished_at and last_success.run_started_at:
                duration_seconds = (last_success.run_finished_at - last_success.run_started_at).total_seconds()
            
            return {
                "total_runs": total,
                "total_records_processed": int(total_records),
                "last_success": {
                    "timestamp": last_success.run_finished_at.isoformat() if last_success and last_success.run_finished_at else None,
                    "records_processed": last_success.records_processed if last_success else None,
                    "duration_seconds": duration_seconds,
                },
                "last_failure": {
                    "timestamp": last_failure.run_finished_at.isoformat() if last_failure and last_failure.run_finished_at else None,
                    "error": last_failure.error if last_failure else None,
                },
            }
