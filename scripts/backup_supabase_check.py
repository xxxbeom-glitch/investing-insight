#!/usr/bin/env python3
"""Backup readiness probe — Free-plan dump/restore evidence (never prints secrets)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api"))
load_dotenv(REPO / ".env.local")
load_dotenv(REPO / ".env")

from app.settings import get_settings  # noqa: E402

EVIDENCE = (
    REPO
    / "audit"
    / "post-mvp"
    / "M01_automation_deployment"
    / "evidence"
    / "backup_readiness.json"
)


def hostname_only(db_url: str) -> str | None:
    if not db_url:
        return None
    try:
        return urlparse(db_url).hostname
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    get_settings.cache_clear()
    s = get_settings()
    host = hostname_only(s.supabase_db_url or "")
    readiness = {}
    if EVIDENCE.is_file():
        readiness = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    backup_ready = bool(readiness.get("ok")) and bool((readiness.get("verify") or {}).get("ok")) and bool(
        (readiness.get("restore_drill") or {}).get("ok")
    )
    # Never unlock production schedulers from this probe on Free-plan path
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_hostname_set": bool(host),
        "db_hostname": host,
        "pitr_available": False,
        "pitr_confirmed": False,
        "backup_method": "free_plan_logical_dump_restore",
        "backup_ready": backup_ready,
        "scheduler_enable_allowed": False,
        "ok": bool(host) and backup_ready,
        "evidence": "audit/post-mvp/M01_automation_deployment/evidence/backup_readiness.json",
    }
    text = json.dumps(report, indent=2)
    print(text)
    out = EVIDENCE.parent / "backup_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
