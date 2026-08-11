#!/usr/bin/env python3
"""M06 governance CLI — proposals require replay+holdout before approve; no auto-apply."""

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

from app.governance.proposals import (  # noqa: E402
    GovernanceError,
    approve_proposal,
    create_proposal,
    freeze_proposal,
    submit_proposal,
)
from app.settings import get_settings  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--artifact-type", required=True)
    c.add_argument("--artifact-ref", required=True)
    c.add_argument("--to-version", required=True)
    c.add_argument("--from-version", default="")
    c.add_argument("--rationale", required=True)
    s = sub.add_parser("submit")
    s.add_argument("--id", required=True)
    a = sub.add_parser("approve")
    a.add_argument("--id", required=True)
    a.add_argument("--replay-notes", required=True)
    a.add_argument("--holdout-notes", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--id", required=True)
    args = p.parse_args()

    get_settings.cache_clear()
    settings = get_settings()
    if not settings.supabase_db_url:
        print(json.dumps({"ok": False, "error_code": "MISSING_DB_URL"}))
        return 2

    try:
        with psycopg.connect(settings.supabase_db_url) as conn:
            if args.cmd == "create":
                out = create_proposal(
                    conn,
                    artifact_type=args.artifact_type,
                    artifact_ref=args.artifact_ref,
                    to_version=args.to_version,
                    from_version=args.from_version or None,
                    rationale=args.rationale,
                )
            elif args.cmd == "submit":
                out = submit_proposal(conn, args.id)
            elif args.cmd == "approve":
                out = approve_proposal(
                    conn,
                    args.id,
                    replay_notes=args.replay_notes,
                    holdout_notes=args.holdout_notes,
                )
            else:
                out = freeze_proposal(conn, args.id)
        print(json.dumps({"ok": True, **out, "scheduler_enable_allowed": False}, indent=2))
        return 0
    except GovernanceError as exc:
        print(json.dumps({"ok": False, "error_code": "GovernanceError", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
