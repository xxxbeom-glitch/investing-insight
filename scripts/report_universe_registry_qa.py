#!/usr/bin/env python3
"""Universe registry QA counts + excluded leakage check (ER-P1-01)."""

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
from app.universe.classify import ALLOWED_EXCHANGES, EXCLUDE_TYPES, UNIVERSE_NAME  # noqa: E402
import psycopg  # noqa: E402


def main() -> int:
    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        print("SUPABASE_DB_URL required", file=sys.stderr)
        return 2
    with psycopg.connect(s.supabase_db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from securities")
            securities_total = cur.fetchone()[0]
            cur.execute("select count(*) from securities where exchange='XNYS'")
            nyse = cur.fetchone()[0]
            cur.execute("select count(*) from securities where exchange='XNAS'")
            nasdaq = cur.fetchone()[0]
            # latest membership per security
            cur.execute(
                """
                with latest as (
                  select distinct on (security_id)
                    security_id, included, exclusion_reason, inclusion_reason, evaluated_at, rule_version
                  from universe_memberships
                  where universe_name=%s
                  order by security_id, evaluated_at desc, included asc, membership_id desc, included asc, membership_id desc
                )
                select
                  count(*) filter (where included),
                  count(*) filter (where not included),
                  count(*) filter (where included and exists (
                    select 1 from securities s where s.security_id=latest.security_id and s.is_adr
                  )),
                  count(*) filter (where included and exists (
                    select 1 from securities s where s.security_id=latest.security_id and not s.is_adr
                  ))
                from latest
                """,
                (UNIVERSE_NAME,),
            )
            included, excluded, included_adr, included_common = cur.fetchone()
            cur.execute(
                """
                with latest as (
                  select distinct on (security_id)
                    security_id, included, exclusion_reason
                  from universe_memberships
                  where universe_name=%s
                  order by security_id, evaluated_at desc, included asc, membership_id desc
                )
                select coalesce(exclusion_reason,'unknown'), count(*)
                from latest
                where not included
                group by 1
                order by 2 desc
                """,
                (UNIVERSE_NAME,),
            )
            exclusions = {r[0]: r[1] for r in cur.fetchall()}
            cur.execute(
                """
                select count(*) from companies where sec_cik is null
                """
            )
            companies_missing_cik = cur.fetchone()[0]
            # leakage: latest included but type/exchange violates rules
            cur.execute(
                """
                with latest as (
                  select distinct on (security_id)
                    security_id, included
                  from universe_memberships
                  where universe_name=%s
                  order by security_id, evaluated_at desc, included asc, membership_id desc
                )
                select count(*)
                from latest l
                join securities s on s.security_id=l.security_id
                where l.included = true
                  and (
                    s.exchange <> all(%s)
                    or s.security_type = any(%s)
                  )
                """,
                (UNIVERSE_NAME, list(ALLOWED_EXCHANGES), list(EXCLUDE_TYPES)),
            )
            leakage = cur.fetchone()[0]
            cur.execute(
                """
                select count(*) from (
                  select exchange, ticker, count(*) c
                  from securities
                  group by 1,2
                  having count(*) > 1
                ) d
                """
            )
            duplicate_exchange_ticker = cur.fetchone()[0]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "finding": "ER-P1-01",
        "universe_name": UNIVERSE_NAME,
        "counts": {
            "securities_total": securities_total,
            "nyse": nyse,
            "nasdaq": nasdaq,
            "included": included,
            "excluded": excluded,
            "included_common": included_common,
            "included_adr": included_adr,
            "companies_missing_cik": companies_missing_cik,
            "duplicate_exchange_ticker_pairs": duplicate_exchange_ticker,
            "excluded_security_leakage": leakage,
        },
        "exclusions_by_reason": exclusions,
        "pass": leakage == 0 and duplicate_exchange_ticker == 0,
    }
    out = REPO / "audit" / "mvp" / "L10_mvp_freeze" / "evidence" / "registry_qa_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"wrote {out}")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
