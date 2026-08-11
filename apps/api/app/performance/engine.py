from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

import psycopg

from app.performance.config import load_performance_rules
from app.performance.metrics import (
    cohort_for_status,
    forward_return,
    price_outcome,
    relative_return,
    thesis_correctness,
)


def _load_prices(
    conn: psycopg.Connection,
    security_id: str,
    *,
    as_of_date: date | None = None,
) -> list[tuple[date, float]]:
    with conn.cursor() as cur:
        if as_of_date is None:
            cur.execute(
                """
                select trading_date, coalesce(adjusted_close, close)::float
                from daily_prices
                where security_id = %s::uuid
                order by trading_date asc
                """,
                (security_id,),
            )
        else:
            cur.execute(
                """
                select trading_date, coalesce(adjusted_close, close)::float
                from daily_prices
                where security_id = %s::uuid
                  and trading_date <= %s
                order by trading_date asc
                """,
                (security_id, as_of_date),
            )
        return [(r[0], float(r[1])) for r in cur.fetchall()]


def _security_id_for_ticker(conn: psycopg.Connection, ticker: str) -> str | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            select security_id::text from securities
            where ticker = %s
            order by updated_at desc nulls last
            limit 1
            """,
            (ticker.upper(),),
        )
        row = cur.fetchone()
        return row[0] if row else None


def evaluate_judgment_horizons(
    conn: psycopg.Connection,
    *,
    judgment_id: str,
    as_of_date: date | None = None,
    rules: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rules = rules or load_performance_rules()
    as_of = as_of_date or date.today()
    version = str(rules.get("version") or "performance-rules-v0.1")

    with conn.cursor() as cur:
        cur.execute(
            """
            select judgment_id::text, run_id::text, security_id::text, status, created_at::date
            from judgments
            where judgment_id = %s::uuid
            """,
            (judgment_id,),
        )
        row = cur.fetchone()
    if not row:
        raise RuntimeError(f"judgment not found: {judgment_id}")

    jid, run_id, security_id, status, created_date = row
    entry_as_of = created_date or as_of
    cohort = cohort_for_status(status, rules)
    prices = _load_prices(conn, security_id, as_of_date=as_of)

    bench_prices: dict[str, list[tuple[date, float]]] = {}
    for b in rules.get("benchmarks") or []:
        sid = _security_id_for_ticker(conn, b)
        if sid:
            bench_prices[b.upper()] = _load_prices(conn, sid, as_of_date=as_of)

    results: list[dict[str, Any]] = []
    for horizon, days in (rules.get("horizons") or {}).items():
        trading_days = int(days)
        fwd = forward_return(
            prices, entry_as_of=entry_as_of, trading_days=trading_days, as_of_date=as_of
        )
        spy_fwd = (
            forward_return(
                bench_prices["SPY"],
                entry_as_of=entry_as_of,
                trading_days=trading_days,
                as_of_date=as_of,
            )
            if "SPY" in bench_prices
            else {"status": "INCOMPLETE", "reason": "spy_missing"}
        )
        qqq_fwd = (
            forward_return(
                bench_prices["QQQ"],
                entry_as_of=entry_as_of,
                trading_days=trading_days,
                as_of_date=as_of,
            )
            if "QQQ" in bench_prices
            else {"status": "INCOMPLETE", "reason": "qqq_missing"}
        )

        if fwd["status"] != "COMPLETE":
            rec = {
                "judgment_id": jid,
                "run_id": run_id,
                "security_id": security_id,
                "judgment_status": status,
                "cohort": cohort,
                "as_of_date": as_of,
                "horizon": horizon,
                "trading_days": trading_days,
                "status": "INCOMPLETE",
                "incomplete_reason": fwd.get("reason"),
                "abs_return": None,
                "spy_return": None,
                "qqq_return": None,
                "rel_spy": None,
                "rel_qqq": None,
                "price_outcome": "unknown",
                "thesis_correctness": thesis_correctness(status, None, rules),
                "entry_date": fwd.get("entry_date"),
                "exit_date": None,
                "entry_price": fwd.get("entry_price"),
                "exit_price": None,
                "rule_version": version,
            }
        else:
            abs_ret = float(fwd["abs_return"])
            spy_ret = spy_fwd.get("abs_return") if spy_fwd.get("status") == "COMPLETE" else None
            qqq_ret = qqq_fwd.get("abs_return") if qqq_fwd.get("status") == "COMPLETE" else None
            incomplete_bits = []
            if spy_ret is None:
                incomplete_bits.append(spy_fwd.get("reason") or "spy_incomplete")
            if qqq_ret is None:
                incomplete_bits.append(qqq_fwd.get("reason") or "qqq_incomplete")
            # Absolute can be COMPLETE even if relative incomplete
            rec = {
                "judgment_id": jid,
                "run_id": run_id,
                "security_id": security_id,
                "judgment_status": status,
                "cohort": cohort,
                "as_of_date": as_of,
                "horizon": horizon,
                "trading_days": trading_days,
                "status": "COMPLETE",
                "incomplete_reason": ",".join(incomplete_bits) if incomplete_bits else None,
                "abs_return": abs_ret,
                "spy_return": spy_ret,
                "qqq_return": qqq_ret,
                "rel_spy": relative_return(abs_ret, spy_ret),
                "rel_qqq": relative_return(abs_ret, qqq_ret),
                "price_outcome": price_outcome(abs_ret),
                "thesis_correctness": thesis_correctness(status, abs_ret, rules),
                "entry_date": fwd["entry_date"],
                "exit_date": fwd["exit_date"],
                "entry_price": fwd["entry_price"],
                "exit_price": fwd["exit_price"],
                "rule_version": version,
            }

        eval_id = str(uuid.uuid4())
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into performance_evals (
                  eval_id, judgment_id, run_id, security_id, judgment_status, cohort,
                  as_of_date, horizon, trading_days, entry_date, exit_date,
                  entry_price, exit_price, abs_return, spy_return, qqq_return,
                  rel_spy, rel_qqq, price_outcome, thesis_correctness,
                  status, incomplete_reason, rule_version
                ) values (
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                on conflict (judgment_id, horizon, as_of_date) do update set
                  abs_return = excluded.abs_return,
                  spy_return = excluded.spy_return,
                  qqq_return = excluded.qqq_return,
                  rel_spy = excluded.rel_spy,
                  rel_qqq = excluded.rel_qqq,
                  price_outcome = excluded.price_outcome,
                  thesis_correctness = excluded.thesis_correctness,
                  status = excluded.status,
                  incomplete_reason = excluded.incomplete_reason,
                  entry_date = excluded.entry_date,
                  exit_date = excluded.exit_date,
                  entry_price = excluded.entry_price,
                  exit_price = excluded.exit_price
                returning eval_id::text
                """,
                (
                    eval_id,
                    rec["judgment_id"],
                    rec["run_id"],
                    rec["security_id"],
                    rec["judgment_status"],
                    rec["cohort"],
                    rec["as_of_date"],
                    rec["horizon"],
                    rec["trading_days"],
                    rec.get("entry_date"),
                    rec.get("exit_date"),
                    rec.get("entry_price"),
                    rec.get("exit_price"),
                    rec.get("abs_return"),
                    rec.get("spy_return"),
                    rec.get("qqq_return"),
                    rec.get("rel_spy"),
                    rec.get("rel_qqq"),
                    rec["price_outcome"],
                    rec["thesis_correctness"],
                    rec["status"],
                    rec.get("incomplete_reason"),
                    rec["rule_version"],
                ),
            )
            rec["eval_id"] = cur.fetchone()[0]
        conn.commit()
        results.append(rec)
    return results


def evaluate_run(
    conn: psycopg.Connection,
    *,
    run_id: str | None = None,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    with conn.cursor() as cur:
        if run_id:
            cur.execute(
                "select judgment_id::text from judgments where run_id=%s::uuid",
                (run_id,),
            )
        else:
            cur.execute(
                """
                select judgment_id::text from judgments
                where run_id = (
                  select run_id from judgments order by created_at desc limit 1
                )
                """
            )
        ids = [r[0] for r in cur.fetchall()]
    all_rows: list[dict[str, Any]] = []
    for jid in ids:
        all_rows.extend(evaluate_judgment_horizons(conn, judgment_id=jid, as_of_date=as_of_date))
    return {
        "run_id": run_id,
        "judgment_count": len(ids),
        "eval_count": len(all_rows),
        "complete": sum(1 for r in all_rows if r["status"] == "COMPLETE"),
        "incomplete": sum(1 for r in all_rows if r["status"] == "INCOMPLETE"),
        "rows": all_rows,
        "scheduler_enable_allowed": False,
    }
