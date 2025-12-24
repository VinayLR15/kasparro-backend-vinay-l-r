import os
import logging
from typing import Iterable, Dict, Any
from sqlalchemy import select
from core.db import SessionLocal, engine
from core.models import RawAsset, Asset, Checkpoint, ETLRun
from ingestion.sources.coinpaprika import CoinPaprikaSource
from ingestion.sources.coingecko import CoinGeckoSource
from ingestion.sources.csv_source import CSVSource
from schemas.asset import AssetSchema
from core.config import settings

logger = logging.getLogger("ingestion")

SOURCE_CLASSES = {
    "coinpaprika": CoinPaprikaSource,
    "coingecko": CoinGeckoSource,
    "csv": CSVSource,
}


def _ensure_tables():
    from core import models
    models.Base.metadata.create_all(bind=engine)


def _process_stream(source_name: str, items: Iterable[Dict[str, Any]], fail_after: int | None = None):
    """Process a stream of items from a single source. Uses its own session."""
    session = SessionLocal()
    processed = 0
    run = None
    try:
        run = ETLRun(source=source_name, status="running")
        session.add(run)
        session.commit()
        
        checkpoint = session.execute(select(Checkpoint).where(Checkpoint.source==source_name)).scalar_one_or_none()
        if not checkpoint:
            checkpoint = Checkpoint(source=source_name, last_record_id=None)
            session.add(checkpoint)
            session.commit()

        last_seen = checkpoint.last_record_id
        for item in items:
            record_id = str(item.get("id") or item.get("raw", {}).get("id") or item.get("record_id"))
            # incremental: if we've already seen this record, skip it (resume after checkpoint)
            if last_seen and record_id == last_seen:
                logger.info("Reached checkpoint record for source %s at %s; skipping to resume", source_name, record_id)
                continue

            # write raw (idempotent)
            exists = session.execute(select(RawAsset).where(RawAsset.source==source_name, RawAsset.record_id==record_id)).scalar_one_or_none()
            if not exists:
                raw = RawAsset(source=source_name, record_id=record_id, payload=item.get("raw") or item)
                session.add(raw)
                session.commit()

            # validate and normalize
            try:
                asset_in = AssetSchema(external_id=record_id, symbol=item.get("symbol"), name=item.get("name"), source=source_name, metadata=item.get("raw"))
            except Exception as e:
                logger.exception("Validation failed for record %s: %s", record_id, e)
                continue

            # upsert asset idempotently
            existing_asset = session.execute(select(Asset).where(Asset.external_id==asset_in.external_id, Asset.source==asset_in.source)).scalar_one_or_none()
            if not existing_asset:
                new_asset = Asset(external_id=asset_in.external_id, symbol=asset_in.symbol, name=asset_in.name, source=asset_in.source, run_metadata=asset_in.metadata)
                session.add(new_asset)
                session.commit()

            # update checkpoint transactionally
            checkpoint.last_record_id = record_id
            session.add(checkpoint)
            session.commit()

            processed += 1
            run.records_processed = processed
            session.add(run)
            session.commit()

            # failure injection (checkpoint already committed above, safe to fail)
            if fail_after and processed >= fail_after:
                run.injected_failure = True
                run.status = "failed"
                session.add(run)
                session.commit()
                raise RuntimeError(f"Injected failure after {processed} records")

        run.status = "success"
        session.add(run)
        session.commit()
    except Exception as e:
        try:
            if run:
                run.status = "failed"
                run.error = str(e)
                session.add(run)
                session.commit()
        except Exception as commit_err:
            logger.exception("Failed to commit error state: %s", commit_err)
            session.rollback()
        logger.exception("ETL run failed for %s", source_name)
        raise
    finally:
        session.close()


def run_all():
    _ensure_tables()
    fail_after_env = settings.ETL_FAIL_AFTER_N_RECORDS
    fail_after = int(fail_after_env) if fail_after_env else None
    # sources in order
    sources = [("coinpaprika", CoinPaprikaSource()), ("coingecko", CoinGeckoSource()), ("csv", CSVSource())]
    for name, src in sources:
        logger.info("Starting source %s", name)
        _process_stream(name, src.list_assets(), fail_after=fail_after)


if __name__ == "__main__":
    run_all()
