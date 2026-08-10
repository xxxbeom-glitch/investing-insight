#!/usr/bin/env python3
"""Backup readiness probe — never prints connection secrets."""

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


def hostname_only(db_url: str) -> str | None:
    if not db_url:
        return None
    try:
        host = urlparse(db_url).hostname
        return host
    except Exception:  # noqa: BLE001
        return None


def pitr_status_confirmed(text: str) -> bool:
    for line in text.splitlines():
        if line.strip() == "Status: CONFIRMED":
            return True
    return False


def main() -> int:
    get_settings.cache_clear()
    s = get_settings()
    evidence = (
        REPO
        / "audit"
        / "post-mvp"
        / "M01_automation_deployment"
        / "evidence"
        / "supabase_pitr_confirmation.md"
    )
    evidence_ok = evidence.is_file() and pitr_status_confirmed(evidence.read_text(encoding="utf-8"))
    host = hostname_only(s.supabase_db_url or "")
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_hostname_set": bool(host),
        "db_hostname": host,
        "pitr_evidence_path": str(evidence.relative_to(REPO)).replace("\\", "/"),
        "pitr_confirmed": evidence_ok,
        "scheduler_enable_allowed": evidence_ok,
        "ok": bool(host) and evidence_ok,
    }
    text = json.dumps(report, indent=2)
    print(text)
    out = evidence.parent / "backup_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
