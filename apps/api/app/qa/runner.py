from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

import psycopg

from app.qa.validate import DataQAError, validate_daily_price_row, validate_fact_row


def quarantine(conn: psycopg.Connection, entity_type: str, entity_ref: str, reason: str, payload: dict[str, Any] | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into data_quarantine (quarantine_id, entity_type, entity_ref, reason, payload)
            values (%s,%s,%s,%s,%s::jsonb)
            """,
            (str(uuid.uuid4()), entity_type, entity_ref, reason, json.dumps(payload or {})),
        )
    conn.commit()


def record_check(conn: psycopg.Connection, dataset: str, check_name: str, status: str, details: dict[str, Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into data_quality_checks (dataset, check_name, status, details)
            values (%s,%s,%s,%s::jsonb)
            """,
            (dataset, check_name, status, json.dumps(details)),
        )
    conn.commit()


def run_daily_price_qa(conn: psycopg.Connection, limit: int = 500) -> dict[str, int]:
    stats = {"checked": 0, "pass": 0, "fail": 0}
    with conn.cursor() as cur:
        cur.execute(
            """
            select security_id::text, trading_date::text, open, high, low, close, volume
            from daily_prices order by collected_at desc limit %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
    for sid, td, o, h, l, c, v in rows:
        stats["checked"] += 1
        payload = {"security_id": sid, "trading_date": td, "open": o, "high": h, "low": l, "close": c, "volume": v}
        try:
            validate_daily_price_row(payload)
            stats["pass"] += 1
        except DataQAError as exc:
            stats["fail"] += 1
            quarantine(conn, "daily_prices", f"{sid}:{td}", str(exc), payload)
    status = "PASS" if stats["fail"] == 0 else "FAIL"
    record_check(conn, "daily_prices", "row_validate", status, stats)
    if stats["fail"] > 0:
        raise DataQAError(f"validated layer blocked: {stats['fail']} daily_prices failures")
    return stats


def run_facts_qa(conn: psycopg.Connection, limit: int = 500) -> dict[str, int]:
    stats = {"checked": 0, "pass": 0, "fail": 0}
    with conn.cursor() as cur:
        cur.execute(
            """
            select fact_id::text, metric_key, value, period_end::text, published_at::text
            from financial_facts order by created_at desc limit %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
    for fact_id, metric, value, pe, pub in rows:
        stats["checked"] += 1
        payload = {"metric_key": metric, "value": value, "period_end": pe, "published_at": pub}
        try:
            validate_fact_row(payload)
            stats["pass"] += 1
        except DataQAError as exc:
            stats["fail"] += 1
            quarantine(conn, "financial_facts", fact_id, str(exc), payload)
    status = "PASS" if stats["fail"] == 0 else "FAIL"
    record_check(conn, "financial_facts", "row_validate", status, stats)
    if stats["fail"] > 0:
        raise DataQAError(f"validated layer blocked: {stats['fail']} financial_facts failures")
    return stats
