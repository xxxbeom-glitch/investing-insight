#!/usr/bin/env python3
"""Biweekly research job entrypoint (scheduler). Fail-closed; no secrets in output."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api"))
load_dotenv(REPO / ".env.local")
load_dotenv(REPO / ".env")

import psycopg  # noqa: E402

from app.ops.jobs import finish_job, start_job  # noqa: E402
from app.quant.config import load_quant_rules  # noqa: E402
from app.quant.engine import run_quant_for_snapshot  # noqa: E402
from app.research.company_research import run_company_research  # noqa: E402
from app.research.judgment import JudgmentPolicyError, run_final_judgment  # noqa: E402
from app.research.openai_responses import ModelUnavailableError, OpenAIResponsesClient  # noqa: E402
from app.research.packet import build_company_packet  # noqa: E402
from app.research.qa import run_research_qa  # noqa: E402
from app.settings import get_settings  # noqa: E402
from app.snapshot.engine import create_snapshot  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Biweekly research with ops_jobs ledger")
    p.add_argument("--limit", type=int, default=1, help="Max priced securities for snapshot scope")
    p.add_argument("--dry-run", action="store_true", help="Create job + resolve candidates only")
    args = p.parse_args()

    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        print(json.dumps({"ok": False, "error_code": "MISSING_DB_URL"}))
        return 2

    summary: dict = {"job_type": "biweekly_research", "limit": args.limit}
    with psycopg.connect(s.supabase_db_url) as conn:
        job_id = start_job(
            conn,
            job_type="biweekly_research",
            stage="init",
            payload={"limit": args.limit},
        )
        summary["job_id"] = job_id
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select security_id::text
                    from (
                      select distinct dp.security_id
                      from daily_prices dp
                    ) t
                    order by security_id
                    limit %s
                    """,
                    (args.limit,),
                )
                security_ids = [r[0] for r in cur.fetchall()]
            if not security_ids:
                raise RuntimeError("no priced securities")

            summary["security_ids"] = security_ids
            if args.dry_run:
                finish_job(
                    conn,
                    job_id,
                    status="success",
                    stage="dry_run",
                    result={"security_ids": security_ids},
                )
                summary["ok"] = True
                summary["dry_run"] = True
                print(json.dumps(summary, indent=2))
                return 0

            if not s.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY missing")

            with conn.cursor() as cur:
                cur.execute(
                    "update ops_jobs set stage=%s where job_id=%s::uuid",
                    ("snapshot", job_id),
                )
            conn.commit()

            snap = create_snapshot(
                conn,
                cutoff_at=datetime.now(timezone.utc),
                code_commit_hash="m01-biweekly",
                security_ids=security_ids,
            )
            quant = run_quant_for_snapshot(
                conn,
                snapshot_id=snap["snapshot_id"],
                run_id=snap["run_id"],
                rules=load_quant_rules(),
            )
            shortlist = quant.get("shortlist") or []
            if not shortlist:
                raise RuntimeError("no quant shortlist")

            client = OpenAIResponsesClient(s)
            researched = 0
            security_id = shortlist[0]
            with conn.cursor() as cur:
                cur.execute(
                    "update ops_jobs set stage=%s where job_id=%s::uuid",
                    (f"research:{security_id[:8]}", job_id),
                )
            conn.commit()
            packet = build_company_packet(
                conn,
                run_id=snap["run_id"],
                snapshot_id=snap["snapshot_id"],
                security_id=security_id,
            )
            research = run_company_research(conn, packet=packet, client=client, settings=s)
            qa = run_research_qa(
                conn,
                packet=packet,
                research_id=research["research_id"],
                research_output=research["output"],
                client=client,
                settings=s,
            )
            try:
                run_final_judgment(
                    conn,
                    packet=packet,
                    qa_id=qa["qa_id"],
                    qa_status=qa["status"],
                    judgment_output=None,
                    client=client,
                    settings=s,
                )
            except JudgmentPolicyError:
                if qa["status"] == "FAIL":
                    watch = {
                        "status": "WATCH",
                        "thesis": "Held for review after QA FAIL",
                        "why_now": "biweekly job",
                        "key_evidence_refs": [],
                        "bear_case": ["qa_fail"],
                        "risks": ["unsupported_claims"],
                        "invalidation_conditions": ["qa remains FAIL"],
                        "validation_horizon": "n/a",
                        "evidence_quality": "D",
                        "data_completeness": 0,
                        "uncertainty": "HIGH",
                    }
                    run_final_judgment(
                        conn,
                        packet=packet,
                        qa_id=qa["qa_id"],
                        qa_status=qa["status"],
                        judgment_output=watch,
                        client=None,
                        settings=s,
                    )
            researched = 1

            finish_job(
                conn,
                job_id,
                status="success",
                stage="done",
                result={"run_id": snap["run_id"], "researched": researched},
            )
            summary["ok"] = True
            summary["run_id"] = snap["run_id"]
            summary["researched"] = researched
            print(json.dumps(summary, indent=2))
            return 0
        except ModelUnavailableError as exc:
            conn.rollback()
            finish_job(
                conn,
                job_id,
                status="failed",
                stage="llm",
                error_code="ModelUnavailableError",
                error_message=str(exc),
            )
            summary["ok"] = False
            summary["error_code"] = "ModelUnavailableError"
            print(json.dumps(summary, indent=2))
            return 1
        except Exception as exc:  # noqa: BLE001
            conn.rollback()
            finish_job(
                conn,
                job_id,
                status="failed",
                stage="error",
                error_code=type(exc).__name__,
                error_message=str(exc),
            )
            summary["ok"] = False
            summary["error_code"] = type(exc).__name__
            print(json.dumps(summary, indent=2))
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
