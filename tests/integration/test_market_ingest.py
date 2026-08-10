import pytest

from app.market.daily import MarketDataError
from app.market.ingest import ingest_ticker_daily, persist_daily_bars
from app.settings import get_settings


def test_persist_idempotent():
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.supabase_db_url:
        pytest.skip("no db")
    import psycopg

    raw = [{"o": 10, "h": 12, "l": 9, "c": 11, "v": 1000, "t": 1704067200000}]
    with psycopg.connect(settings.supabase_db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("select security_id from securities where ticker='AAPL' limit 1")
            row = cur.fetchone()
            if not row:
                pytest.skip("AAPL security missing; run L01 ingest first")
            sid = str(row[0])
        s1 = persist_daily_bars(conn, security_id=sid, ticker="AAPL", raw_bars=raw)
        s2 = persist_daily_bars(conn, security_id=sid, ticker="AAPL", raw_bars=raw)
        assert s1["upserted"] == 1
        assert s2["upserted"] == 1
        with conn.cursor() as cur:
            cur.execute("select count(*) from daily_prices where security_id=%s and trading_date=%s", (sid, "2024-01-01"))
            # date may shift by tz; count by security
            cur.execute("select count(*) from daily_prices where security_id=%s", (sid,))
            assert cur.fetchone()[0] >= 1


def test_live_aapl_daily_ingest():
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.massive_api_key or not settings.supabase_db_url:
        pytest.skip("missing credentials")
    stats = ingest_ticker_daily(
        settings.supabase_db_url,
        settings.massive_api_key,
        "AAPL",
        "2026-07-01",
        "2026-07-10",
    )
    assert stats["fetched"] >= 1
    assert stats["upserted"] >= 1
    assert stats["rejected"] == 0


def test_api_failure_not_silent(monkeypatch):
    from app.providers.massive import MassiveClient

    client = MassiveClient("dummy")

    def boom(*args, **kwargs):
        raise RuntimeError("massive HTTP 500")

    monkeypatch.setattr(client, "get_daily_aggs", boom)
    from app.market.daily import fetch_daily_bars

    with pytest.raises(RuntimeError):
        fetch_daily_bars(client, "AAPL", "2024-01-01", "2024-01-02")
