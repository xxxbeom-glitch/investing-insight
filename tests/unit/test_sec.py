import time

import pytest

from app.sec.client import RateLimiter, SecClient
from app.sec.facts import build_ticker_cik_map, extract_fact_points


def test_rate_limiter_spacing():
    lim = RateLimiter(max_per_sec=5)
    t0 = time.monotonic()
    for _ in range(3):
        lim.wait()
    elapsed = time.monotonic() - t0
    assert elapsed >= 0.35  # ~0.2s * 2 gaps


def test_build_ticker_cik_map():
    payload = {"0": {"ticker": "aapl", "cik_str": 320193, "title": "Apple"}}
    m = build_ticker_cik_map(payload)
    assert m["AAPL"] == "0000320193"


def test_extract_fact_points_period_published():
    payload = {
        "cik": 320193,
        "entityName": "Apple Inc.",
        "facts": {
            "us-gaap": {
                "Assets": {
                    "units": {
                        "USD": [
                            {"val": 1, "end": "2023-09-30", "filed": "2023-11-03", "fy": 2023, "fp": "FY", "form": "10-K", "accn": "0001"}
                        ]
                    }
                }
            }
        },
    }
    rows = extract_fact_points(payload, metrics=["Assets"])
    assert len(rows) == 1
    assert rows[0]["period_end"] == "2023-09-30"
    assert rows[0]["published_at"] == "2023-11-03"
    assert rows[0]["period_end"] != rows[0]["published_at"]


def test_sec_client_requires_ua():
    with pytest.raises(RuntimeError):
        SecClient("   ")


def test_sec_403_not_silent(monkeypatch):
    client = SecClient("investing-insight/0.1 test@example.com")

    class FakeRes:
        status_code = 403
        text = "forbidden"

    def fake_get(*args, **kwargs):
        return FakeRes()

    monkeypatch.setattr("app.sec.client.httpx.get", fake_get)
    with pytest.raises(RuntimeError, match="403"):
        client.get_json("https://example.invalid")
