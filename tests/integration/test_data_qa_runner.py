import pytest

from app.qa.runner import run_daily_price_qa, run_facts_qa
from app.qa.validate import DataQAError
from app.settings import get_settings


def test_run_qa_on_db():
    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        pytest.skip("no db")
    import psycopg

    with psycopg.connect(s.supabase_db_url) as conn:
        d = run_daily_price_qa(conn)
        f = run_facts_qa(conn)
        assert d["fail"] == 0
        assert f["fail"] == 0
        with conn.cursor() as cur:
            cur.execute("select count(*) from data_quality_checks where status='PASS'")
            assert cur.fetchone()[0] >= 2
