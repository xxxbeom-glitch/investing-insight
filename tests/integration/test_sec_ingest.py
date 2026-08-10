import pytest

from app.sec.ingest import ingest_sec_sample
from app.settings import get_settings


def test_sec_live_sample_aapl():
    get_settings.cache_clear()
    s = get_settings()
    if not s.sec_user_agent or not s.supabase_db_url:
        pytest.skip("missing sec/db")
    stats = ingest_sec_sample(s.supabase_db_url, s.sec_user_agent, ["AAPL"])
    assert stats["tickers_mapped"] >= 0
    assert stats["facts_rows"] > 0
    # reruns may insert 0 due to immutable fact_id conflict-do-nothing
    import psycopg

    with psycopg.connect(s.supabase_db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from financial_facts")
            assert cur.fetchone()[0] > 0
