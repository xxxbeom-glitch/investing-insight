#!/usr/bin/env python3
"""M04 performance tracking evaluator (deterministic)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api"))
load_dotenv(REPO / ".env.local")
load_dotenv(REPO / ".env")

import psycopg  # noqa: E402

from app.ops.jobs import finish_job, start_job  # noqa: E402
from app.performance.engine import evaluate_run  # noqa: E402
from app.settings import get_settings  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", default="")
    p.add_argument("--as-of", default="", help="YYYY-MM-DD")
    args = p.parse_args()

    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        print(json.dumps({"ok": False, "error_code": "MISSING_DB_URL"}))
        return 2

    as_of = date.fromisoformat(args.as_of) if args.as_of else None
    with psycopg.connect(s.supabase_db_url) as conn:
        job_id = start_job(conn, job_type="performance_eval", stage="init", payload={})
        try:
            result = evaluate_run(conn, run_id=args.run_id or None, as_of_date=as_of)
            # strip bulky rows for stdout summary
            summary = {
                "ok": True,
                "job_id": job_id,
                "scheduler_enable_allowed": False,
                "judgment_count": result["judgment_count"],
                "eval_count": result["eval_count"],
                "complete": result["complete"],
                "incomplete": result["incomplete"],
                "sample": [
                    {
                        "judgment_id": r["judgment_id"],
                        "horizon": r["horizon"],
                        "cohort": r["cohort"],
                        "status": r["status"],
                        "abs_return": r.get("abs_return"),
                        "rel_spy": r.get("rel_spy"),
                        "thesis_correctness": r.get("thesis_correctness"),
                        "price_outcome": r.get("price_outcome"),
                    }
                    for r in result["rows"][:12]
                ],
            }
            finish_job(
                conn,
                job_id,
                status="success",
                stage="done",
                result={
                    "eval_count": result["eval_count"],
                    "complete": result["complete"],
                    "incomplete": result["incomplete"],
                },
            )
            print(json.dumps(summary, indent=2, default=str))
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
            print(json.dumps({"ok": False, "error_code": type(exc).__name__, "job_id": job_id}, indent=2))
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
