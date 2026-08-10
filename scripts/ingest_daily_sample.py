#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api"))
load_dotenv(REPO / ".env.local")
load_dotenv(REPO / ".env")

from app.settings import get_settings  # noqa: E402
from app.market.ingest import ingest_ticker_daily  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ticker", default="AAPL")
    p.add_argument("--start", default="2026-07-01")
    p.add_argument("--end", default="2026-07-31")
    args = p.parse_args()
    get_settings.cache_clear()
    s = get_settings()
    stats = ingest_ticker_daily(s.supabase_db_url, s.massive_api_key, args.ticker, args.start, args.end)
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
