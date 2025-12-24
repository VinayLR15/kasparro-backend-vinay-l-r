import pytest
import ingestion.run
from core.models import ETLRun, Checkpoint, RawAsset, Asset


@pytest.fixture(autouse=False)
def inject_failure_env(monkeypatch):
    """Helper fixture for setting failure injection."""
    def _set_fail_after(n):
        monkeypatch.setenv("ETL_FAIL_AFTER_N_RECORDS", str(n))
        # Reload config to pick up env var
        from importlib import reload
        import core.config
        reload(core.config)
    return _set_fail_after


def test_etl_runs_and_writes():
    """Test ETL runs end-to-end and writes records idempotently.
    Patch external sources to avoid network calls and keep test fast.
    """
    class EmptySource:
        def list_assets(self):
            if False:
                yield

    # patch external API sources to be empty; CSVSource will read the local test CSV
    import ingestion.run as irun
    import importlib
    importlib.reload(irun)
    irun.CoinPaprikaSource = lambda: EmptySource()
    irun.CoinGeckoSource = lambda: EmptySource()

    # run ETL once (uses CSV from ingestion/data/assets.csv)
    ingestion.run.run_all()
    # run again to test idempotency (should not duplicate)
    ingestion.run.run_all()
    # check that assets table has entries
    from core.db import SessionLocal
    with SessionLocal() as s:
        count = s.query(Asset).count()
        assert count >= 2


def test_failure_injection_and_recovery(monkeypatch):
    """Test failure injection, recovery, and idempotency."""
    # Use deterministic DummySource to avoid external API calls
    class DummySource:
        def __init__(self):
            self.items = [
                {"id": "r1", "symbol": "S1", "name": "N1", "raw": {"id": "r1"}},
                {"id": "r2", "symbol": "S2", "name": "N2", "raw": {"id": "r2"}},
                {"id": "r3", "symbol": "S3", "name": "N3", "raw": {"id": "r3"}},
            ]

        def list_assets(self):
            for i in self.items:
                yield i

    class EmptySource:
        def list_assets(self):
            if False:
                yield

    # Patch ingestion.run sources: make coinpaprika/coingecko empty, csv produce our dummy items
    monkeypatch.setattr(ingestion.run, "CoinPaprikaSource", lambda: EmptySource())
    monkeypatch.setattr(ingestion.run, "CoinGeckoSource", lambda: EmptySource())
    monkeypatch.setattr(ingestion.run, "CSVSource", lambda: DummySource())

    # === PHASE 1: Inject failure after 1 record ===
    monkeypatch.setenv("ETL_FAIL_AFTER_N_RECORDS", "1")
    from importlib import reload
    import core.config
    reload(core.config)

    # reload ingestion.run so it picks up the updated settings, then reapply source patches
    import importlib
    importlib.reload(ingestion.run)
    monkeypatch.setattr(ingestion.run, "CoinPaprikaSource", lambda: EmptySource())
    monkeypatch.setattr(ingestion.run, "CoinGeckoSource", lambda: EmptySource())
    monkeypatch.setattr(ingestion.run, "CSVSource", lambda: DummySource())

    # Run ETL and expect it to fail
    with pytest.raises(Exception):
        ingestion.run.run_all()

    # Verify failed run recorded with checkpoint saved
    from core.db import SessionLocal
    with SessionLocal() as s:
        failed_runs = s.query(ETLRun).filter(ETLRun.source == "csv", ETLRun.status == "failed").all()
        assert len(failed_runs) >= 1, "No failed run found"

        ck = s.query(Checkpoint).filter(Checkpoint.source == "csv").one_or_none()
        assert ck is not None, "No checkpoint found"
        assert ck.last_record_id == "r1", f"Checkpoint points to {ck.last_record_id}, not r1"

        raw_count = s.query(RawAsset).filter(RawAsset.source == "csv").count()
        asset_count = s.query(Asset).count()
        assert raw_count == 1, f"Expected 1 raw record, got {raw_count}"
        assert asset_count == 1, f"Expected 1 asset, got {asset_count}"

    # === PHASE 2: Resume without failure injection ===
    monkeypatch.delenv("ETL_FAIL_AFTER_N_RECORDS", raising=False)
    reload(core.config)

    # reload ingestion.run again after removing env var and reapply patches
    import importlib
    importlib.reload(ingestion.run)
    monkeypatch.setattr(ingestion.run, "CoinPaprikaSource", lambda: EmptySource())
    monkeypatch.setattr(ingestion.run, "CoinGeckoSource", lambda: EmptySource())
    monkeypatch.setattr(ingestion.run, "CSVSource", lambda: DummySource())

    # Run ETL again; should resume from checkpoint and succeed
    ingestion.run.run_all()

    from core.db import SessionLocal
    with SessionLocal() as s:
        success_runs = s.query(ETLRun).filter(ETLRun.source == "csv", ETLRun.status == "success").all()
        assert len(success_runs) >= 1, "No successful run found"

        ck = s.query(Checkpoint).filter(Checkpoint.source == "csv").one_or_none()
        assert ck.last_record_id == "r3", f"Checkpoint should be r3, got {ck.last_record_id}"

        # Should have exactly 3 assets, no duplicates
        asset_count = s.query(Asset).count()
        assert asset_count == 3, f"Expected 3 assets total, got {asset_count}"

    # === PHASE 3: Verify idempotency ===
    ingestion.run.run_all()
    from core.db import SessionLocal
    with SessionLocal() as s:
        final_count = s.query(Asset).count()
        assert final_count == 3, f"Idempotency check failed: got {final_count} assets"
