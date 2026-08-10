#!/usr/bin/env python3
"""Gate 0 production readiness probes — never print secret values."""

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

from app.llm_profiles import load_llm_profiles  # noqa: E402
from app.settings import get_settings  # noqa: E402


REQUIRED_DOCS = [
    REPO / "docs" / "ops" / "PRODUCTION_READINESS.md",
    REPO / "docs" / "ops" / "RUNBOOK_BACKUP_RESTORE.md",
    REPO / "docs" / "ops" / "RUNBOOK_SECRET_ROTATION.md",
    REPO / "docs" / "ops" / "RUNBOOK_FAILURE_QUARANTINE.md",
    REPO / "docs" / "ops" / "RUNBOOK_HEALTH_MONITORING.md",
]

SECRET_NEEDLES = ("BEGIN PRIVATE", "password=", "PASSWORD=")


def _looks_like_secret_blob(text: str) -> bool:
    """Heuristic: key-shaped / connection-string material — not short prose mentions."""
    lower = text.lower()
    if "postgresql://" in lower:
        return True
    if "eyJ" in text and len(text) > 80:
        return True
    if "sk-" in text:
        for token in text.replace("\n", " ").split():
            if token.startswith("sk-") and len(token) >= 20:
                return True
    if any(n.lower() in lower for n in SECRET_NEEDLES):
        return True
    return False


def build_report() -> dict:
    get_settings.cache_clear()
    s = get_settings()
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": ok, "detail": detail[:300]})

    for doc in REQUIRED_DOCS:
        add(f"doc:{doc.name}", doc.is_file(), str(doc.relative_to(REPO)))

    add("supabase_url_set", bool(s.supabase_url), "flag_only")
    add("supabase_secret_set", bool(s.supabase_secret_key), "flag_only")
    add("supabase_db_set", bool(s.supabase_db_url), "flag_only")
    add("openai_key_set", bool(s.openai_api_key), "flag_only")
    add("massive_key_set", bool(s.massive_api_key), "flag_only")
    add("sec_ua_set", bool(s.sec_user_agent), "flag_only")

    try:
        profiles = load_llm_profiles()
        add("llm_profiles_load", True, profiles.version)
        add(
            "llm_roles_present",
            all(hasattr(profiles, r) for r in ("company_research", "research_qa", "final_judgment")),
            "company_research/research_qa/final_judgment",
        )
    except Exception as exc:  # noqa: BLE001
        add("llm_profiles_load", False, type(exc).__name__)

    # ensure serialized report cannot contain raw secrets from settings
    blob = json.dumps(
        {
            "supabase_url_set": bool(s.supabase_url),
            "openai_key_set": bool(s.openai_api_key),
            "db_set": bool(s.supabase_db_url),
        }
    )
    add("report_payload_no_raw_secret", not _looks_like_secret_blob(blob), "flags_only_json")

    # scan ops docs for accidental key-shaped material (heuristic)
    docs_clean = True
    for doc in REQUIRED_DOCS:
        if doc.is_file() and _looks_like_secret_blob(doc.read_text(encoding="utf-8")):
            docs_clean = False
            break
    add("ops_docs_heuristic_clean", docs_clean, "no key-shaped blobs")

    ok = all(c["ok"] for c in checks)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate": "G00",
        "pass": ok,
        "checks": checks,
    }


def main() -> int:
    report = build_report()
    text = json.dumps(report, indent=2)
    if _looks_like_secret_blob(text):
        print("REFUSING TO PRINT: secret-like content detected in report", file=sys.stderr)
        return 2
    print(text)
    out = REPO / "audit" / "post-mvp" / "G00_production_readiness" / "evidence" / "readiness_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
