from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.settings import get_settings
from app.snapshot.engine import create_snapshot, validate_snapshot_manifest


def test_validate_snapshot_manifest_schema_keys():
    validate_snapshot_manifest(
        {
            "snapshot_id": "s",
            "run_id": "r",
            "cutoff_at": "2026-08-10T00:00:00+00:00",
            "content_hash": "abc",
            "source_versions": [],
            "config_versions": {"universe_rule_version": "u"},
        }
    )
    with pytest.raises(ValueError):
        validate_snapshot_manifest({"snapshot_id": "s"})


def test_snapshot_deterministic_and_no_future():
    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        pytest.skip("no db")
    import psycopg

    assert (Path("packages/schemas/snapshot_manifest.schema.json")).exists()
    cutoff = datetime.now(timezone.utc)
    with psycopg.connect(s.supabase_db_url) as conn:
        a = create_snapshot(conn, cutoff_at=cutoff, code_commit_hash="test")
        b = create_snapshot(conn, cutoff_at=cutoff, code_commit_hash="test")
        assert a["content_hash"] == b["content_hash"]
        assert a["snapshot_id"] == b["snapshot_id"]
        assert b.get("reused") is True
        assert a["counts"]["universe_membership"] >= 1
        with conn.cursor() as cur:
            cur.execute("select manifest from snapshots where snapshot_id=%s", (a["snapshot_id"],))
            row = cur.fetchone()
            assert row is not None
            validate_snapshot_manifest(row[0])
            cur.execute(
                """
                select count(*) from snapshot_items si
                where si.snapshot_id = %s
                  and si.item_type='daily_price'
                  and (si.payload->>'trading_date')::date > %s
                """,
                (a["snapshot_id"], cutoff.date()),
            )
            assert cur.fetchone()[0] == 0
            cur.execute(
                """
                select count(*) from snapshot_items si
                where si.snapshot_id = %s
                  and si.item_type='financial_fact'
                  and coalesce(
                    (si.payload->>'published_at')::date,
                    (si.payload->>'filed_at')::date
                  ) > %s
                """,
                (a["snapshot_id"], cutoff.date()),
            )
            assert cur.fetchone()[0] == 0
