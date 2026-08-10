#!/usr/bin/env python3
"""M02 Top-down slice: FRED → regime → industry → QA → value-chain → candidates → union."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api"))
load_dotenv(REPO / ".env.local")
load_dotenv(REPO / ".env")

import psycopg  # noqa: E402

from app.macro.fred_client import FredClient, FredUnavailableError  # noqa: E402
from app.macro.ingest import ingest_fred_series, latest_by_role  # noqa: E402
from app.macro.regime import classify_regime, load_industry_rules, persist_regime  # noqa: E402
from app.ops.jobs import finish_job, start_job  # noqa: E402
from app.settings import get_settings  # noqa: E402
from app.topdown.engine import (  # noqa: E402
    industry_qa,
    load_value_chain,
    promote_topdown_candidates,
    run_industry_assessments,
    snapshot_value_chains,
    union_shortlists,
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--skip-fred-fetch", action="store_true", help="Use existing macro_observations only")
    p.add_argument("--bottom-up-run-id", default="", help="Optional quant run_id for union")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    get_settings.cache_clear()
    s = get_settings()
    summary: dict = {"job_type": "topdown_slice", "scheduler_enable_allowed": False}
    if not s.supabase_db_url:
        print(json.dumps({"ok": False, "error_code": "MISSING_DB_URL"}))
        return 2

    with psycopg.connect(s.supabase_db_url) as conn:
        job_id = start_job(conn, job_type="topdown_slice", stage="init", payload={})
        summary["job_id"] = job_id
        try:
            if args.dry_run:
                rules = load_industry_rules()
                chain = load_value_chain()
                finish_job(
                    conn,
                    job_id,
                    status="success",
                    stage="dry_run",
                    result={
                        "industries": len(rules.get("industries") or []),
                        "chains": len(chain.get("chains") or []),
                    },
                )
                summary.update({"ok": True, "dry_run": True})
                print(json.dumps(summary, indent=2))
                return 0

            if not args.skip_fred_fetch:
                if not s.fred_api_key:
                    raise FredUnavailableError("FRED_API_KEY missing")
                client = FredClient(s.fred_api_key)
                with conn.cursor() as cur:
                    cur.execute(
                        "update ops_jobs set stage=%s where job_id=%s::uuid",
                        ("fred_ingest", job_id),
                    )
                conn.commit()
                fred_stats = ingest_fred_series(conn, client)
                summary["fred"] = fred_stats

            latest = latest_by_role(conn)
            if not latest:
                raise RuntimeError("no macro observations")
            classified = classify_regime(latest)
            regime_id = persist_regime(conn, classified)
            summary["regime"] = {"regime_id": regime_id, "regime": classified["regime"], "as_of": classified["as_of"]}

            assessments = run_industry_assessments(
                conn,
                regime_id=regime_id,
                regime=classified["regime"],
                as_of=classified["as_of"],
                latest=latest,
            )
            rules = load_industry_rules()
            block = bool((rules.get("qa") or {}).get("block_on_fail", True))
            chains = {c["industry_id"]: c.get("nodes") or [] for c in (load_value_chain().get("chains") or [])}
            snapshot_value_chains(conn)

            promoted = []
            pass_assessment_ids = []
            for a in assessments:
                qa = industry_qa(conn, a, rules)
                a["qa"] = qa
                nodes = chains.get(a["industry_id"]) or []
                cands = promote_topdown_candidates(
                    conn,
                    assessment=a,
                    qa_status=qa["status"],
                    chain_nodes=nodes,
                    block_on_fail=block,
                )
                if qa["status"] == "PASS":
                    pass_assessment_ids.append(a["assessment_id"])
                    promoted.extend(cands)

            bottom = args.bottom_up_run_id or None
            if not bottom:
                with conn.cursor() as cur:
                    cur.execute(
                        "select run_id::text from research_runs order by created_at desc limit 1"
                    )
                    row = cur.fetchone()
                    bottom = row[0] if row else None

            union = union_shortlists(
                conn,
                as_of=classified["as_of"],
                assessment_ids=pass_assessment_ids,
                bottom_up_run_id=bottom,
            )
            finish_job(
                conn,
                job_id,
                status="success",
                stage="done",
                result={
                    "regime": classified["regime"],
                    "assessments": len(assessments),
                    "promoted": len(promoted),
                    "union_id": union["union_id"],
                    "union_members": union["member_count"],
                },
            )
            summary.update(
                {
                    "ok": True,
                    "assessments": [
                        {
                            "industry_id": a["industry_id"],
                            "overall": a["scores"]["overall"],
                            "qa": a["qa"]["status"],
                        }
                        for a in assessments
                    ],
                    "promoted_count": len(promoted),
                    "union": {"union_id": union["union_id"], "member_count": union["member_count"]},
                }
            )
            print(json.dumps(summary, indent=2))
            return 0
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
            summary.update({"ok": False, "error_code": type(exc).__name__})
            # never echo secrets
            print(json.dumps(summary, indent=2))
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
