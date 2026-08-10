import json
from pathlib import Path

import pytest

from app.settings import get_settings
from app.universe.ingest import ingest_from_massive, persist_tickers

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "universe_tickers.json"


def test_persist_fixtures_to_db():
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.supabase_db_url:
        pytest.skip("SUPABASE_DB_URL not set")
    import psycopg

    rows = json.loads(FIX.read_text(encoding="utf-8"))
    with psycopg.connect(settings.supabase_db_url) as conn:
        stats = persist_tickers(conn, rows)
        assert stats["seen"] == len(rows)
        assert stats["included"] >= 3
        assert stats["excluded"] >= 1
        with conn.cursor() as cur:
            cur.execute("select count(*) from securities")
            assert cur.fetchone()[0] >= 1
            cur.execute(
                "select count(*) from universe_memberships where included = true and exclusion_reason is null"
            )
            assert cur.fetchone()[0] >= 1
            cur.execute(
                "select count(*) from universe_memberships where included = false and exclusion_reason is not null"
            )
            assert cur.fetchone()[0] >= 1


def test_massive_live_sample():
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.massive_api_key:
        pytest.skip("MASSIVE_API_KEY not set")
    if not settings.supabase_db_url:
        pytest.skip("SUPABASE_DB_URL not set")
    stats = ingest_from_massive(
        settings.supabase_db_url,
        settings.massive_api_key,
        tickers=["AAPL", "IBM", "BABA", "SPY"],
    )
    assert stats["seen"] == 4
    assert stats["included"] >= 2
    assert stats["excluded"] >= 1
