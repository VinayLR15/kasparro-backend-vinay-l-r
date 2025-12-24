import pytest
from fastapi.testclient import TestClient
from api.main import app


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert "db" in r.json()


def test_data_and_stats():
    client = TestClient(app)
    r = client.get("/data")
    assert r.status_code == 200
    s = client.get("/stats")
    assert s.status_code == 200
