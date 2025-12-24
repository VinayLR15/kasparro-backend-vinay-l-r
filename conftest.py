"""pytest configuration: isolated test database setup."""
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


@pytest.fixture(scope="function", autouse=True)
def isolated_test_db(monkeypatch):
    """
    Set up isolated SQLite DB for each test.
    Cleans up all resources after test completes.
    """
    # Create temporary DB file
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()
    
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    
    # Create isolated test engine and session factory
    test_engine = create_engine(db_url, future=True, connect_args={"timeout": 30})
    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
    TestBase = declarative_base()
    
    # Make core modules use test DB for this test
    import core.models
    core.models.Base.metadata.create_all(bind=test_engine)
    
    # Monkeypatch core.db to use test engine
    import core.db
    original_engine = core.db.engine
    original_sessionlocal = core.db.SessionLocal
    core.db.engine = test_engine
    core.db.SessionLocal = TestSessionLocal
    
    yield
    
    # Cleanup: close all connections and dispose engine
    try:
        # close any sessions created by the test session factory
        if hasattr(TestSessionLocal, "close_all_sessions"):
            TestSessionLocal.close_all_sessions()
        elif hasattr(TestSessionLocal, "close_all"):
            TestSessionLocal.close_all()
    except Exception:
        pass

    try:
        test_engine.dispose()
    except Exception:
        pass

    # Restore original engine/session and dispose original engine to avoid lingering pools
    try:
        core.db.engine = original_engine
        core.db.SessionLocal = original_sessionlocal
        if original_engine is not None:
            try:
                original_engine.dispose()
            except Exception:
                pass
    except Exception:
        pass

    # Clean up temp file
    try:
        os.unlink(db_path)
    except Exception:
        pass
