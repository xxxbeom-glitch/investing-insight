from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_v1_settings_summary_no_raw_secrets():
    res = client.get("/v1/settings/summary")
    assert res.status_code == 200
    body = res.json()
    blob = str(body)
    assert "openai_key_set" in body["providers"]
    assert "sk-" not in blob
    assert "OPENAI_API_KEY" not in blob


def test_v1_dashboard_and_runs():
    d = client.get("/v1/dashboard")
    assert d.status_code in {200, 503}
    if d.status_code == 200:
        assert "counts" in d.json()
        r = client.get("/v1/runs")
        assert r.status_code == 200
        assert "runs" in r.json()
