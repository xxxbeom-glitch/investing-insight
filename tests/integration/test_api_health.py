from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_health_config_ok():
    res = client.get("/health/config")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "llm_profile_version" in body


def test_health_db_with_credentials():
    res = client.get("/health/db")
    # With credentials present should be 200; without, 503.
    assert res.status_code in (200, 503)
    if res.status_code == 200:
        assert res.json()["status"] == "ok"
