from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.quant.config import load_quant_rules
from app.quant.engine import run_quant_for_snapshot
from app.research.claim_check import deterministic_qa
from app.research.judgment import JudgmentPolicyError, run_final_judgment
from app.research.packet import build_company_packet
from app.research.qa import run_research_qa
from app.settings import get_settings
from app.snapshot.engine import create_snapshot


def _prep(conn):
    snap = create_snapshot(conn, cutoff_at=datetime.now(timezone.utc), code_commit_hash="l08")
    run_quant_for_snapshot(
        conn, snapshot_id=snap["snapshot_id"], run_id=snap["run_id"], rules=load_quant_rules()
    )
    with conn.cursor() as cur:
        cur.execute(
            "select security_id::text from quant_scores where run_id=%s order by rank_market limit 1",
            (snap["run_id"],),
        )
        row = cur.fetchone()
    if not row:
        pytest.skip("no scored securities")
    packet = build_company_packet(
        conn, run_id=snap["run_id"], snapshot_id=snap["snapshot_id"], security_id=row[0]
    )
    return snap, packet


def test_qa_fail_blocks_selected_and_judgment_immutable():
    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        pytest.skip("no db")
    import psycopg

    with psycopg.connect(s.supabase_db_url) as conn:
        snap, packet = _prep(conn)
        bad_research = {
            "summary": "Invented revenue 888888",
            "business_model": "x",
            "bull_case": ["a"],
            "bear_case": ["b"],
            "key_risks": ["c"],
            "invalidation_conditions": ["d"],
            "uncertainties": ["e"],
            "claim_evidence_map": [{"claim": "888888 profit", "evidence_id": "missing"}],
            "unsupported_or_missing": [],
        }
        assert deterministic_qa(packet, bad_research)["status"] == "FAIL"

        # insert stub ai_research row for FK
        research_id = str(uuid4())
        execution_id = str(uuid4())
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into llm_executions (
                  execution_id, run_id, security_id, agent_role, prompt_version, llm_profile_version,
                  requested_model, reasoning_effort, input_hash, schema_version, status
                ) values (%s,%s,%s,'company_research','p','llm-profile-v0.1','gpt-5.6-terra','medium','h','s','succeeded')
                """,
                (execution_id, packet["run_id"], packet["security_id"]),
            )
            cur.execute(
                """
                insert into ai_research (research_id, execution_id, run_id, security_id, output_json, output_hash)
                values (%s,%s,%s,%s,%s::jsonb,'h')
                """,
                (
                    research_id,
                    execution_id,
                    packet["run_id"],
                    packet["security_id"],
                    __import__("json").dumps(bad_research),
                ),
            )
        conn.commit()

        qa = run_research_qa(
            conn, packet=packet, research_id=research_id, research_output=bad_research, client=None
        )
        assert qa["status"] == "FAIL"
        assert qa["requested_model"] == "gpt-5.6-terra"
        assert qa["reasoning_effort"] == "high"

        selected = {
            "status": "SELECTED",
            "thesis": "t",
            "why_now": "n",
            "key_evidence_refs": [],
            "bear_case": ["bear"],
            "risks": ["risk"],
            "invalidation_conditions": ["inv"],
            "validation_horizon": "12m",
            "evidence_quality": "B",
            "data_completeness": 50,
            "uncertainty": "HIGH",
        }
        with pytest.raises(JudgmentPolicyError):
            run_final_judgment(
                conn,
                packet=packet,
                qa_id=qa["qa_id"],
                qa_status=qa["status"],
                judgment_output=selected,
            )

        watch = {
            **selected,
            "status": "WATCH",
            "key_evidence_refs": [packet["evidence"][0]["evidence_id"]] if packet["evidence"] else [],
        }
        if not packet["evidence"]:
            watch["key_evidence_refs"] = []
        # empty refs ok for WATCH
        j = run_final_judgment(
            conn,
            packet=packet,
            qa_id=qa["qa_id"],
            qa_status=qa["status"],
            judgment_output={**watch, "key_evidence_refs": []},
        )
        assert j["status"] == "WATCH"
        with conn.cursor() as cur:
            with pytest.raises(Exception):
                cur.execute(
                    "update judgments set thesis='mutated' where judgment_id=%s",
                    (j["judgment_id"],),
                )
                conn.commit()
            conn.rollback()
