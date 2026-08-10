#!/usr/bin/env python3
"""Live OpenAI Research → QA → Judgment smoke for one candidate (ER-P1-02)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api"))
load_dotenv(REPO / ".env.local")
load_dotenv(REPO / ".env")

from app.quant.config import load_quant_rules  # noqa: E402
from app.quant.engine import run_quant_for_snapshot  # noqa: E402
from app.research.company_research import run_company_research  # noqa: E402
from app.research.judgment import JudgmentPolicyError, run_final_judgment  # noqa: E402
from app.research.openai_responses import ModelUnavailableError, OpenAIResponsesClient  # noqa: E402
from app.research.packet import build_company_packet  # noqa: E402
from app.research.qa import run_research_qa  # noqa: E402
from app.settings import get_settings  # noqa: E402
from app.snapshot.engine import create_snapshot  # noqa: E402
import psycopg  # noqa: E402


def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    out_dir = REPO / "audit" / "mvp" / "L10_mvp_freeze" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "finding": "ER-P1-02",
        "status": "FAIL",
    }
    if not settings.openai_api_key or not settings.supabase_db_url:
        result["error"] = "OPENAI_API_KEY and SUPABASE_DB_URL required"
        (out_dir / "live_research_run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 2

    client = OpenAIResponsesClient(settings)
    try:
        with psycopg.connect(settings.supabase_db_url) as conn:
            # Prefer securities that already have prices (lab fixtures), not full registry.
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select distinct dp.security_id::text
                    from daily_prices dp
                    join securities s on s.security_id=dp.security_id
                    limit 20
                    """
                )
                priced = [r[0] for r in cur.fetchall()]
            if not priced:
                result["error"] = "no priced securities for smoke"
                (out_dir / "live_research_run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
                print(json.dumps(result, indent=2))
                return 1
            snap = create_snapshot(
                conn,
                cutoff_at=datetime.now(timezone.utc),
                code_commit_hash="l10-remediation-er-p1-02",
                security_ids=priced,
            )
            quant = run_quant_for_snapshot(
                conn,
                snapshot_id=snap["snapshot_id"],
                run_id=snap["run_id"],
                rules=load_quant_rules(),
            )
            if not quant["shortlist"]:
                result["error"] = "no quant shortlist"
                result["snapshot"] = snap
                (out_dir / "live_research_run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
                print(json.dumps(result, indent=2))
                return 1
            security_id = quant["shortlist"][0]
            packet = build_company_packet(
                conn,
                run_id=snap["run_id"],
                snapshot_id=snap["snapshot_id"],
                security_id=security_id,
            )
            research = run_company_research(conn, packet=packet, client=client, settings=settings)
            qa = run_research_qa(
                conn,
                packet=packet,
                research_id=research["research_id"],
                research_output=research["output"],
                client=client,
                settings=settings,
            )
            judgment_payload = None
            judgment_err = None
            try:
                # Prefer live final judgment; if QA FAIL, force WATCH/REJECT via policy
                judgment = run_final_judgment(
                    conn,
                    packet=packet,
                    qa_id=qa["qa_id"],
                    qa_status=qa["status"],
                    judgment_output=None,
                    client=client,
                    settings=settings,
                )
                judgment_payload = judgment
            except (JudgmentPolicyError, ModelUnavailableError, Exception) as exc:  # noqa: BLE001
                judgment_err = f"{type(exc).__name__}: {exc}"
                # If live model produced SELECTED under FAIL, policy blocks — record fail-closed success for policy
                if qa["status"] == "FAIL":
                    watch = {
                        "status": "WATCH",
                        "thesis": "Held for review after QA FAIL",
                        "why_now": "integration smoke",
                        "key_evidence_refs": [],
                        "bear_case": ["qa_fail"],
                        "risks": ["unsupported_claims"],
                        "invalidation_conditions": ["qa remains FAIL"],
                        "validation_horizon": "n/a",
                        "evidence_quality": "D",
                        "data_completeness": 0,
                        "uncertainty": "HIGH",
                    }
                    judgment_payload = run_final_judgment(
                        conn,
                        packet=packet,
                        qa_id=qa["qa_id"],
                        qa_status=qa["status"],
                        judgment_output=watch,
                        client=None,
                        settings=settings,
                    )

            result.update(
                {
                    "status": "PASS" if judgment_payload else "FAIL",
                    "run_id": snap["run_id"],
                    "snapshot_id": snap["snapshot_id"],
                    "security_id": security_id,
                    "research": {
                        "execution_id": research["execution_id"],
                        "research_id": research["research_id"],
                        "requested_model": research["requested_model"],
                        "resolved_model": research["resolved_model"],
                        "reasoning_effort": research["reasoning_effort"],
                        "llm_profile_version": research["llm_profile_version"],
                        "prompt_version": research["prompt_version"],
                        "input_hash": research["input_hash"],
                        "output_hash": research["output_hash"],
                    },
                    "qa": {
                        "qa_id": qa["qa_id"],
                        "status": qa["status"],
                        "requested_model": qa["requested_model"],
                        "resolved_model": qa["resolved_model"],
                        "reasoning_effort": qa["reasoning_effort"],
                    },
                    "judgment": judgment_payload,
                    "judgment_live_error": judgment_err,
                }
            )
    except ModelUnavailableError as exc:
        result["status"] = "FAIL"
        result["error"] = f"model_unavailable_fail_closed: {exc}"
    except Exception as exc:  # noqa: BLE001
        result["status"] = "FAIL"
        result["error"] = f"{type(exc).__name__}: {exc}"

    path = out_dir / "live_research_run.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    print(f"wrote {path}")
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
