#!/usr/bin/env python3
"""M03 multi-agent pipeline. Default --mock (no live spend). Use --live for OpenAI."""

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

from app.agents.mock_client import MockStructuredClient  # noqa: E402
from app.agents.orchestrator import run_multi_agent_pipeline  # noqa: E402
from app.ops.jobs import finish_job, start_job  # noqa: E402
from app.research.openai_responses import OpenAIResponsesClient  # noqa: E402
from app.settings import get_settings  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true", default=True)
    p.add_argument("--live", action="store_true", help="Use OpenAI Responses (not mock)")
    p.add_argument("--security-limit", type=int, default=1)
    p.add_argument("--dry-run", action="store_true", help="Bind only; do not run agents")
    args = p.parse_args()
    use_live = bool(args.live)

    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        print(json.dumps({"ok": False, "error_code": "MISSING_DB_URL"}))
        return 2

    summary: dict = {"job_type": "multi_agent", "scheduler_enable_allowed": False, "mode": "live" if use_live else "mock"}
    with psycopg.connect(s.supabase_db_url) as conn:
        job_id = start_job(conn, job_type="multi_agent", stage="init", payload={"mode": summary["mode"]})
        summary["job_id"] = job_id
        try:
            if args.dry_run:
                from app.agents.binding import bind_multi_agent_run
                from app.agents.profiles import load_multiagent_profiles

                profiles = load_multiagent_profiles()
                binding = bind_multi_agent_run(
                    conn,
                    llm_profile_version=profiles.version,
                    security_limit=args.security_limit,
                )
                finish_job(
                    conn,
                    job_id,
                    status="success",
                    stage="dry_run",
                    result={"snapshot_id": binding["snapshot_id"], "multi_agent_run_id": binding["multi_agent_run_id"]},
                )
                summary.update({"ok": True, "dry_run": True, **{k: binding[k] for k in ("multi_agent_run_id", "snapshot_id", "run_id")}})
                print(json.dumps(summary, indent=2))
                return 0

            if use_live:
                if not s.openai_api_key:
                    raise RuntimeError("OPENAI_API_KEY missing")
                client = OpenAIResponsesClient(s)
            else:
                client = MockStructuredClient()

            result = run_multi_agent_pipeline(
                conn,
                client=client,
                settings=s,
                security_limit=args.security_limit,
            )
            if result.get("ok"):
                finish_job(conn, job_id, status="success", stage="done", result={"snapshot_id": result["snapshot_id"]})
            elif result.get("blocked"):
                finish_job(
                    conn,
                    job_id,
                    status="failed",
                    stage="blocked",
                    error_code="GateBlockedError",
                    error_message=result.get("error"),
                )
            else:
                finish_job(
                    conn,
                    job_id,
                    status="failed",
                    stage="error",
                    error_code=result.get("error_code"),
                    error_message=result.get("error"),
                )
            summary.update(result)
            print(json.dumps(summary, indent=2, default=str))
            return 0 if result.get("ok") else 1
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
            print(json.dumps(summary, indent=2))
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
