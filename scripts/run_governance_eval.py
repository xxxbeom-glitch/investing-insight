#!/usr/bin/env python3
"""Run deterministic replay/holdout evaluator and persist governance_evaluations (ER2-P1-03)."""

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

from app.governance.evaluator import (  # noqa: E402
    EvaluatorError,
    run_holdout_evaluation,
    run_replay_evaluation,
)
from app.settings import get_settings  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--kind", required=True, choices=["replay", "holdout"])
    p.add_argument("--artifact-type", required=True)
    p.add_argument("--artifact-ref", required=True)
    p.add_argument("--to-version", required=True)
    args = p.parse_args()

    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        print(json.dumps({"ok": False, "error_code": "MISSING_DB_URL"}))
        return 2
    try:
        with psycopg.connect(s.supabase_db_url) as conn:
            fn = run_replay_evaluation if args.kind == "replay" else run_holdout_evaluation
            out = fn(
                conn,
                artifact_type=args.artifact_type,
                artifact_ref=args.artifact_ref,
                candidate_version=args.to_version,
            )
        print(json.dumps({"ok": True, **out, "scheduler_enable_allowed": False}, indent=2, default=str))
        return 0 if out.get("status") == "PASS" else 1
    except EvaluatorError as exc:
        print(json.dumps({"ok": False, "error_code": "EvaluatorError", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
