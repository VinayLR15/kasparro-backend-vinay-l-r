import os
import logging
from typing import Iterable, Dict, Any
from sqlalchemy import select, func as sql_func
from sqlalchemy.exc import IntegrityError
from core.db import SessionLocal, engine
from core.models import RawAsset, Coin, CoinSource, Checkpoint, ETLRun
from ingestion.sources.coinpaprika import CoinPaprikaSource
from ingestion.sources.coingecko import CoinGeckoSource
from ingestion.sources.csv_source import CSVSource
from core.config import settings

logger = logging.getLogger("ingestion")

SOURCE_CLASSES = {
    "coinpaprika": CoinPaprikaSource,
    "coingecko": CoinGeckoSource,
    "csv": CSVSource,
}


def _ensure_tables():
    """Ensure database tables exist with retry logic."""
    import time
    from core import models
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            models.Base.metadata.create_all(bind=engine)
            logger.info("Database tables verified/created")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Failed to create tables (attempt {attempt + 1}/{max_retries}): {e}. Retrying...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to create tables after {max_retries} attempts: {e}")
                raise


def _normalize_symbol(symbol: str | None) -> str | None:
    """Normalize symbol for matching (uppercase, strip whitespace)."""
    if not symbol:
        return None
    return symbol.strip().upper()


def _find_or_create_canonical_coin(session, symbol: str, name: str | None = None) -> Coin:
    """
    Find existing canonical coin by symbol (case-insensitive) or create new one.
    Updates name if provided name is better (longer/more descriptive).
    Handles race conditions where multiple processes might try to create the same coin.
    """
    normalized_symbol = _normalize_symbol(symbol)
    if not normalized_symbol:
        raise ValueError(f"Invalid symbol: {symbol}")
    
    # Find existing coin by normalized symbol (case-insensitive match for safety)
    coin = session.execute(
        select(Coin).where(sql_func.upper(Coin.symbol) == normalized_symbol)
    ).scalar_one_or_none()
    
    if coin:
        # Update name if new name is better (longer and not empty)
        if name and name.strip() and (not coin.name or len(name.strip()) > len(coin.name or "")):
            coin.name = name.strip()
            session.add(coin)
        return coin
    
    # Create new canonical coin (normalized symbol ensures uniqueness)
    # Handle potential race condition where another process created the coin between query and insert
    try:
        coin = Coin(symbol=normalized_symbol, name=name.strip() if name else None)
        session.add(coin)
        session.flush()  # Get the coin.id, may raise IntegrityError if duplicate
        return coin
    except IntegrityError:
        # Race condition: another process created the coin, query again
        session.rollback()
        coin = session.execute(
            select(Coin).where(sql_func.upper(Coin.symbol) == normalized_symbol)
        ).scalar_one_or_none()
        if coin:
            return coin
        raise  # Re-raise if coin still not found (shouldn't happen)


def _process_stream(source_name: str, items: Iterable[Dict[str, Any]], fail_after: int | None = None):
    """
    Process a stream of items from a single source with normalization.
    Creates canonical coins unified by symbol and links source data to them.
    """
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
            symbol = item.get("symbol")
            name = item.get("name")
            
            # Skip if missing critical fields
            if not record_id or not symbol:
                logger.warning("Skipping item with missing record_id or symbol: %s", item)
                continue
            
            # incremental: if we've already seen this record, skip it (resume after checkpoint)
            if last_seen and record_id == last_seen:
                logger.info("Reached checkpoint record for source %s at %s; skipping to resume", source_name, record_id)
                continue

            # write raw (idempotent)
            exists_raw = session.execute(
                select(RawAsset).where(RawAsset.source==source_name, RawAsset.record_id==record_id)
            ).scalar_one_or_none()
            if not exists_raw:
                raw = RawAsset(source=source_name, record_id=record_id, payload=item.get("raw") or item)
                session.add(raw)
                session.commit()

            # Normalization: Find or create canonical coin by symbol
            try:
                coin = _find_or_create_canonical_coin(session, symbol, name)
                session.commit()
            except Exception as e:
                logger.exception("Failed to find/create canonical coin for symbol %s: %s", symbol, e)
                continue

            # Link source data to canonical coin (idempotent)
            existing_source = session.execute(
                select(CoinSource).where(
                    CoinSource.source==source_name,
                    CoinSource.external_id==record_id
                )
            ).scalar_one_or_none()
            
            if not existing_source:
                # Check if this coin already has a mapping from this source
                existing_coin_source = session.execute(
                    select(CoinSource).where(
                        CoinSource.coin_id==coin.id,
                        CoinSource.source==source_name
                    )
                ).scalar_one_or_none()
                
                if existing_coin_source:
                    # Log warning and skip if external_id differs
                    if existing_coin_source.external_id != record_id:
                        logger.warning(
                            "Skipping %s: already mapped to %s from source %s, new=%s",
                            coin.symbol, existing_coin_source.external_id, source_name, record_id
                        )
                        continue
                else:
                    # Create new source mapping
                    coin_source = CoinSource(
                        coin_id=coin.id,
                        source=source_name,
                        external_id=record_id,
                        source_metadata=item.get("raw") or item
                    )
                    session.add(coin_source)
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
    """Run ETL for all sources with error handling."""
    try:
        _ensure_tables()
    except Exception as e:
        logger.error(f"Failed to ensure tables: {e}. ETL will skip this run.")
        return
    
    fail_after_env = settings.ETL_FAIL_AFTER_N_RECORDS
    fail_after = int(fail_after_env) if fail_after_env else None
    
    any_failed = False
    # sources in order
    sources = [("coinpaprika", CoinPaprikaSource()), ("coingecko", CoinGeckoSource()), ("csv", CSVSource())]
    for name, src in sources:
        try:
            logger.info("Starting source %s", name)
            _process_stream(name, src.list_assets(), fail_after=fail_after)
        except Exception as e:
            logger.exception("Failed to process source %s: %s. Continuing with next source.", name, e)
            any_failed = True
            continue
            
    if any_failed:
        raise RuntimeError("One or more ETL sources failed")


if __name__ == "__main__":
    run_all()
