#!/usr/bin/env python3
"""Full current NYSE/NASDAQ stocks registry ingest via Massive (ER-P1-01)."""

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

from app.settings import get_settings  # noqa: E402
from app.universe.ingest import ingest_from_massive  # noqa: E402


def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.massive_api_key or not settings.supabase_db_url:
        print("MASSIVE_API_KEY and SUPABASE_DB_URL required", file=sys.stderr)
        return 2
    # Full pagination; skip per-ticker raw files to keep remediation tractable (hash still in sources).
    print("ingest XNYS+XNAS full registry (throttled)...", flush=True)
    stats = ingest_from_massive(
        settings.supabase_db_url,
        settings.massive_api_key,
        tickers=None,
        max_pages=None,
        write_raw_files=False,
        exchanges=["XNYS", "XNAS"],
    )
    print("ingest done", flush=True)
    out_dir = REPO / "audit" / "mvp" / "L10_mvp_freeze" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "finding": "ER-P1-01",
        "ingest_stats": stats,
        "note": "raw files skipped; sources.raw_hash retained (db-only storage_path)",
    }
    path = out_dir / "registry_ingest_stats.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
