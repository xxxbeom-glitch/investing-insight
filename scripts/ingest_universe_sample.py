#!/usr/bin/env python3
"""Ingest a small Massive ticker sample into Supabase universe tables."""

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
from app.universe.ingest import ingest_from_massive  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", default="AAPL,IBM,BABA,SPY")
    args = parser.parse_args()
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.massive_api_key or not settings.supabase_db_url:
        print("MASSIVE_API_KEY and SUPABASE_DB_URL required", file=sys.stderr)
        return 2
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    stats = ingest_from_massive(settings.supabase_db_url, settings.massive_api_key, tickers=tickers)
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
