import json

import pytest

from app.agents.binding import verify_frozen_context
from app.settings import get_settings


def test_frozen_context_hash_verify_and_update_forbidden():
    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        pytest.skip("no db")
    import psycopg

    with psycopg.connect(s.supabase_db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select multi_agent_run_id::text from multi_agent_runs
                order by created_at desc limit 1
                """
            )
            row = cur.fetchone()
        if not row:
            pytest.skip("no multi_agent_runs")
        mid = row[0]
        frozen = verify_frozen_context(conn, mid)
        assert frozen
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    update multi_agent_runs
                    set frozen_context = %s::jsonb
                    where multi_agent_run_id=%s::uuid
                    """,
                    (json.dumps({**frozen, "tamper": True}), mid),
                )
                conn.commit()
                pytest.fail("frozen_context update should be forbidden")
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                assert "immutable" in str(exc).lower()
