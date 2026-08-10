#!/usr/bin/env python3
"""Daily market + SEC ingest job (scheduler entrypoint). Fail-closed; no secrets in output."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api"))
load_dotenv(REPO / ".env.local")
load_dotenv(REPO / ".env")

import psycopg  # noqa: E402

from app.market.ingest import ingest_ticker_daily  # noqa: E402
from app.ops.jobs import finish_job, start_job  # noqa: E402
from app.sec.ingest import ingest_sec_sample  # noqa: E402
from app.settings import get_settings  # noqa: E402


def _resolve_tickers(conn: psycopg.Connection, args: argparse.Namespace) -> list[str]:
    if args.tickers:
        return [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    with conn.cursor() as cur:
        cur.execute(
            """
            select s.ticker
            from universe_memberships m
            join securities s on s.security_id = m.security_id
            where m.included = true
            group by s.ticker
            order by s.ticker
            limit %s
            """,
            (args.limit,),
        )
        rows = [r[0] for r in cur.fetchall()]
    if not rows:
        raise RuntimeError("no included tickers found")
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description="Daily market+SEC ingest with ops_jobs ledger")
    p.add_argument("--tickers", default="", help="Comma tickers; default: included universe")
    p.add_argument("--limit", type=int, default=5, help="Max tickers when using universe (default 5)")
    p.add_argument("--start", default="", help="YYYY-MM-DD (default: 7 days ago)")
    p.add_argument("--end", default="", help="YYYY-MM-DD (default: today)")
    p.add_argument("--skip-sec", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="Resolve tickers only; no provider calls")
    args = p.parse_args()

    end = args.end or date.today().isoformat()
    start = args.start or (date.today() - timedelta(days=7)).isoformat()

    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        print(json.dumps({"ok": False, "error_code": "MISSING_DB_URL"}))
        return 2
    if not args.dry_run and not s.massive_api_key:
        print(json.dumps({"ok": False, "error_code": "MISSING_MASSIVE_KEY"}))
        return 2

    summary: dict = {"job_type": "daily_ingest", "start": start, "end": end}
    with psycopg.connect(s.supabase_db_url) as conn:
        job_id = start_job(
            conn,
            job_type="daily_ingest",
            stage="init",
            payload={"start": start, "end": end, "limit": args.limit},
        )
        summary["job_id"] = job_id
        try:
            tickers = _resolve_tickers(conn, args)
            summary["tickers"] = tickers
            if args.dry_run:
                finish_job(conn, job_id, status="success", stage="dry_run", result={"tickers": tickers})
                summary["ok"] = True
                summary["dry_run"] = True
                print(json.dumps(summary, indent=2))
                return 0

            market_stats = []
            for t in tickers:
                with conn.cursor() as cur:
                    cur.execute(
                        "update ops_jobs set stage=%s where job_id=%s::uuid",
                        (f"market:{t}", job_id),
                    )
                conn.commit()
                market_stats.append(ingest_ticker_daily(s.supabase_db_url, s.massive_api_key, t, start, end))

            sec_stats = None
            if not args.skip_sec:
                if not s.sec_user_agent:
                    raise RuntimeError("SEC_USER_AGENT missing")
                with conn.cursor() as cur:
                    cur.execute(
                        "update ops_jobs set stage=%s where job_id=%s::uuid",
                        ("sec", job_id),
                    )
                conn.commit()
                sec_stats = ingest_sec_sample(s.supabase_db_url, s.sec_user_agent, tickers)

            result = {"market": market_stats, "sec": sec_stats}
            finish_job(conn, job_id, status="success", stage="done", result={"ticker_count": len(tickers)})
            summary["ok"] = True
            summary["market_tickers"] = len(market_stats)
            summary["sec"] = sec_stats
            print(json.dumps(summary, indent=2))
            return 0
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
            summary["ok"] = False
            summary["error_code"] = type(exc).__name__
            print(json.dumps(summary, indent=2))
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
