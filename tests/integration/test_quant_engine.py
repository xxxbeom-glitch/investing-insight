from datetime import datetime, timezone

import pytest

from app.settings import get_settings
from app.snapshot.engine import create_snapshot
from app.quant.config import load_quant_rules
from app.quant.engine import run_quant_for_snapshot
from tests.conftest import priced_security_ids


def test_quant_deterministic_no_llm():
    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        pytest.skip("no db")
    import psycopg

    rules = load_quant_rules()
    cutoff = datetime.now(timezone.utc)
    with psycopg.connect(s.supabase_db_url) as conn:
        ids = priced_security_ids(conn)
        if not ids:
            pytest.skip("no priced securities")
        snap = create_snapshot(conn, cutoff_at=cutoff, code_commit_hash="quant-test", security_ids=ids)
        a = run_quant_for_snapshot(conn, snapshot_id=snap["snapshot_id"], run_id=snap["run_id"], rules=rules)
        b = run_quant_for_snapshot(conn, snapshot_id=snap["snapshot_id"], run_id=snap["run_id"], rules=rules)
        assert a["scored"] == b["scored"]
        assert a["rule_version"] == rules.version
        assert a["shortlist"] == b["shortlist"]
        with conn.cursor() as cur:
            cur.execute(
                """
                select count(*), count(distinct input_hash), min(rule_version)
                from quant_scores where run_id=%s
                """,
                (snap["run_id"],),
            )
            n, hashes, ver = cur.fetchone()
            assert n == a["scored"]
            assert hashes >= 1
            assert ver == rules.version
            cur.execute(
                "select total_score from quant_scores where run_id=%s order by rank_market, security_id",
                (snap["run_id"],),
            )
            scores = [float(r[0]) for r in cur.fetchall()]
        with psycopg.connect(s.supabase_db_url) as conn2:
            run_quant_for_snapshot(conn2, snapshot_id=snap["snapshot_id"], run_id=snap["run_id"], rules=rules)
            with conn2.cursor() as cur:
                cur.execute(
                    "select total_score from quant_scores where run_id=%s order by rank_market, security_id",
                    (snap["run_id"],),
                )
                scores2 = [float(r[0]) for r in cur.fetchall()]
        assert scores == scores2
