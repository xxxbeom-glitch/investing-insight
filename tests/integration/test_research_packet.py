import json
from datetime import datetime, timezone

import pytest

from app.quant.config import load_quant_rules
from app.quant.engine import run_quant_for_snapshot
from app.research.company_research import run_company_research
from app.research.openai_responses import ModelUnavailableError, ResponsesResult
from app.research.packet import build_company_packet, persist_packet
from app.research.schema_validate import load_schema, validate_against_schema
from app.settings import get_settings
from app.snapshot.engine import create_snapshot


class FakeOkClient:
    def create_structured(self, **kwargs):
        assert kwargs["model"] == "gpt-5.6-terra"
        assert kwargs["reasoning_effort"] == "medium"
        out = {
            "summary": "Test summary",
            "business_model": "Software",
            "growth_drivers": ["product"],
            "moat_assessment": "moderate",
            "financial_interpretation": "stable",
            "valuation_interpretation": "fair",
            "bull_case": ["growth"],
            "bear_case": ["competition"],
            "key_risks": ["execution"],
            "invalidation_conditions": ["revenue decline"],
            "uncertainties": ["macro"],
            "claim_evidence_map": [],
            "unsupported_or_missing": ["filings excerpts not in packet"],
        }
        return ResponsesResult(
            response_id="resp_fake",
            resolved_model=kwargs["model"],
            output_text=json.dumps(out),
            raw={"model": kwargs["model"]},
            token_usage={"input_tokens": 1, "output_tokens": 1},
        )


class FakeFallbackClient:
    def create_structured(self, **kwargs):
        return ResponsesResult(
            response_id="resp_bad",
            resolved_model="gpt-something-else",
            output_text="{}",
            raw={"model": "gpt-something-else"},
            token_usage=None,
        )


def _prep_run(conn):
    from tests.conftest import priced_security_ids

    ids = priced_security_ids(conn)
    if not ids:
        pytest.skip("no priced securities")
    snap = create_snapshot(
        conn, cutoff_at=datetime.now(timezone.utc), code_commit_hash="l07", security_ids=ids
    )
    run_quant_for_snapshot(
        conn, snapshot_id=snap["snapshot_id"], run_id=snap["run_id"], rules=load_quant_rules()
    )
    with conn.cursor() as cur:
        cur.execute(
            """
            select security_id::text from quant_scores
            where run_id=%s order by rank_market limit 1
            """,
            (snap["run_id"],),
        )
        row = cur.fetchone()
    if not row:
        pytest.skip("no scored securities")
    return snap, row[0]


def test_packet_snapshot_evidence_only_and_schema():
    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        pytest.skip("no db")
    import psycopg

    with psycopg.connect(s.supabase_db_url) as conn:
        snap, sid = _prep_run(conn)
        packet = build_company_packet(
            conn, run_id=snap["run_id"], snapshot_id=snap["snapshot_id"], security_id=sid
        )
        validate_against_schema(packet, load_schema("company_analysis_input.schema.json"))
        assert packet["snapshot_id"] == snap["snapshot_id"]
        for ev in packet["evidence"]:
            assert "evidence_id" in ev
            assert ev["kind"] in {"daily_price", "financial_fact"}
        for series in packet["financial_trends"].values():
            for point in series:
                assert point["evidence_id"].startswith("fact:")
        persisted = persist_packet(conn, packet=packet)
        assert persisted["input_hash"]


def test_company_research_records_hashes_no_silent_fallback():
    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        pytest.skip("no db")
    import psycopg

    with psycopg.connect(s.supabase_db_url) as conn:
        snap, sid = _prep_run(conn)
        packet = build_company_packet(
            conn, run_id=snap["run_id"], snapshot_id=snap["snapshot_id"], security_id=sid
        )
        result = run_company_research(conn, packet=packet, client=FakeOkClient(), settings=s)
        assert result["requested_model"] == result["resolved_model"] == "gpt-5.6-terra"
        assert result["reasoning_effort"] == "medium"
        assert result["input_hash"] and result["output_hash"]
        assert result["llm_profile_version"]
        assert "unsupported_or_missing" in result["output"]

        packet2 = build_company_packet(
            conn, run_id=snap["run_id"], snapshot_id=snap["snapshot_id"], security_id=sid
        )
        with pytest.raises(ModelUnavailableError):
            run_company_research(conn, packet=packet2, client=FakeFallbackClient(), settings=s)
