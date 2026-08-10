from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import psycopg
import yaml

from app.research.schema_validate import load_schema, validate_against_schema

PACKET_SCHEMA_VERSION = "company-analysis-input-v0.1"
PACKET_VERSION = "packet-v0.1"
_LIMITS_PATH = Path(__file__).resolve().parents[4] / "config" / "research_limits.v0.1.yaml"


def load_research_limits(path: Path | None = None) -> dict[str, Any]:
    return yaml.safe_load((path or _LIMITS_PATH).read_text(encoding="utf-8")) or {}


def _hash(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def build_company_packet(
    conn: psycopg.Connection,
    *,
    run_id: str,
    snapshot_id: str,
    security_id: str,
) -> dict[str, Any]:
    limits = load_research_limits()
    max_evidence = int(limits.get("max_evidence_items") or 200)
    max_prices = int(limits.get("max_price_points") or 60)
    max_chars = int(limits.get("max_packet_chars") or 80000)

    with conn.cursor() as cur:
        cur.execute(
            """
            select ticker, exchange, company_id::text
            from securities where security_id=%s
            """,
            (security_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"security not found: {security_id}")
        ticker, exchange, company_id = row

        cur.execute(
            """
            select payload from snapshot_items
            where snapshot_id=%s and item_type='universe_membership' and item_ref=%s
            """,
            (snapshot_id, security_id),
        )
        membership = cur.fetchone()
        if not membership:
            raise ValueError("security not in snapshot membership")

        cur.execute(
            """
            select total_score, growth_score, quality_score, cashflow_score, health_score,
                   valuation_score, momentum_score, rank_market, rule_version, input_hash, missing_components
            from quant_scores where run_id=%s and security_id=%s
            """,
            (run_id, security_id),
        )
        q = cur.fetchone()
        if not q:
            raise ValueError("quant score missing for security")

        cur.execute(
            """
            select item_ref, payload from snapshot_items
            where snapshot_id=%s and item_type='daily_price'
              and payload->>'security_id'=%s
            order by payload->>'trading_date'
            """,
            (snapshot_id, security_id),
        )
        price_rows = cur.fetchall()[-max_prices:]

        cur.execute(
            """
            select item_ref, payload from snapshot_items
            where snapshot_id=%s and item_type='financial_fact'
              and payload->>'company_id'=%s
            order by payload->>'period_end' desc
            """,
            (snapshot_id, company_id),
        )
        fact_rows = cur.fetchall()

    evidence: list[dict[str, Any]] = []
    prices: list[dict[str, Any]] = []
    for item_ref, payload in price_rows:
        eid = f"price:{item_ref}"
        evidence.append(
            {
                "evidence_id": eid,
                "kind": "daily_price",
                "ref": item_ref,
                "trading_date": payload.get("trading_date"),
                "close": payload.get("close"),
            }
        )
        prices.append(
            {
                "trading_date": payload.get("trading_date"),
                "close": payload.get("close"),
                "evidence_id": eid,
            }
        )

    financial_trends: dict[str, list[dict[str, Any]]] = {}
    for item_ref, payload in fact_rows:
        if len(evidence) >= max_evidence:
            break
        eid = f"fact:{item_ref}"
        metric = payload["metric_key"]
        evidence.append(
            {
                "evidence_id": eid,
                "kind": "financial_fact",
                "ref": item_ref,
                "metric_key": metric,
                "value": payload.get("value"),
                "period_end": payload.get("period_end"),
                "published_at": payload.get("published_at"),
                "source_id": payload.get("source_id"),
            }
        )
        financial_trends.setdefault(metric, []).append(
            {
                "value": payload.get("value"),
                "period_end": payload.get("period_end"),
                "evidence_id": eid,
            }
        )

    missing = list(q[10] or [])
    if not prices:
        missing.append("daily_prices")
    if not financial_trends:
        missing.append("financial_facts")

    packet = {
        "schema_version": PACKET_SCHEMA_VERSION,
        "run_id": run_id,
        "snapshot_id": snapshot_id,
        "security_id": security_id,
        "identity": {
            "ticker": ticker,
            "exchange": exchange,
            "company_id": company_id,
            "membership": membership[0],
        },
        "price_metrics": {"series": prices},
        "financial_trends": financial_trends,
        "quant": {
            "total_score": float(q[0]),
            "growth_score": float(q[1]),
            "quality_score": float(q[2]),
            "cashflow_score": float(q[3]),
            "health_score": float(q[4]),
            "valuation_score": float(q[5]),
            "momentum_score": float(q[6]),
            "rank_market": int(q[7]),
            "rule_version": q[8],
            "input_hash": q[9],
        },
        "filings": [],
        "peer_context": {},
        "missing_or_limited": missing,
        "evidence": evidence[:max_evidence],
    }
    schema = load_schema("company_analysis_input.schema.json")
    validate_against_schema(packet, schema)
    blob = json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
    if len(blob) > max_chars:
        raise ValueError(f"packet exceeds max_packet_chars={max_chars}")
    return packet


def persist_packet(
    conn: psycopg.Connection,
    *,
    packet: dict[str, Any],
) -> dict[str, Any]:
    packet_id = str(uuid4())
    input_hash = _hash(packet)
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into research_packets (
              packet_id, run_id, security_id, snapshot_id,
              packet_schema_version, packet_version, input_hash, payload_json
            ) values (%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
            on conflict (run_id, security_id, packet_version) do update
              set payload_json=excluded.payload_json,
                  input_hash=excluded.input_hash,
                  snapshot_id=excluded.snapshot_id
            returning packet_id::text, input_hash
            """,
            (
                packet_id,
                packet["run_id"],
                packet["security_id"],
                packet["snapshot_id"],
                PACKET_SCHEMA_VERSION,
                PACKET_VERSION,
                input_hash,
                json.dumps(packet),
            ),
        )
        pid, ih = cur.fetchone()
    conn.commit()
    return {"packet_id": pid, "input_hash": ih, "packet": packet}
