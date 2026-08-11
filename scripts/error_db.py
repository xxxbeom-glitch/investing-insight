#!/usr/bin/env python3
"""Record / list structured research error events (M05)."""

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

from app.errors.db import InvalidErrorType, list_error_events, load_error_taxonomy, record_error_event  # noqa: E402
from app.settings import get_settings  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--type", required=True)
    a.add_argument("--summary", required=True)
    a.add_argument("--severity", default="P2")
    a.add_argument("--judgment-id", default="")
    a.add_argument("--run-id", default="")
    l = sub.add_parser("list")
    l.add_argument("--type", default="")
    l.add_argument("--limit", type=int, default=20)
    t = sub.add_parser("taxonomy")
    args = p.parse_args()

    if args.cmd == "taxonomy":
        print(json.dumps(load_error_taxonomy(), indent=2))
        return 0

    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        print(json.dumps({"ok": False, "error_code": "MISSING_DB_URL"}))
        return 2

    with psycopg.connect(s.supabase_db_url) as conn:
        if args.cmd == "add":
            try:
                rec = record_error_event(
                    conn,
                    error_type=args.type,
                    summary=args.summary,
                    severity=args.severity,
                    judgment_id=args.judgment_id or None,
                    run_id=args.run_id or None,
                )
            except InvalidErrorType as exc:
                print(json.dumps({"ok": False, "error_code": "InvalidErrorType", "error": str(exc)}))
                return 1
            print(json.dumps({"ok": True, **rec, "scheduler_enable_allowed": False}, indent=2))
            return 0
        rows = list_error_events(conn, error_type=args.type or None, limit=args.limit)
        print(json.dumps({"ok": True, "count": len(rows), "rows": rows}, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
