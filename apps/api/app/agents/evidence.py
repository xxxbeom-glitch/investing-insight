"""Load Snapshot/frozen evidence for multi-agent role packets (ER-P1-02)."""

from __future__ import annotations

import json
from typing import Any

import psycopg


def load_evidence_bundle(
    conn: psycopg.Connection,
    *,
    snapshot_id: str,
    security_id: str,
    frozen_context: dict[str, Any],
    max_prices: int = 40,
    max_facts: int = 40,
) -> dict[str, Any]:
    """Build allowed evidence set from sealed Snapshot + frozen top-down context."""
    evidence: list[dict[str, Any]] = []
    allowed: set[str] = set()

    # Frozen context evidence ids
    regime = frozen_context.get("regime") or {}
    if regime:
        eid = "regime"
        allowed.add(eid)
        evidence.append({"evidence_id": eid, "kind": "regime", "payload": regime})
    for a in frozen_context.get("assessments") or []:
        eid = f"assessment:{a.get('industry_id')}"
        allowed.add(eid)
        aid = a.get("assessment_id")
        if aid:
            allowed.add(f"assessment_id:{aid}")
        evidence.append({"evidence_id": eid, "kind": "industry_assessment", "payload": a})
    union = frozen_context.get("union") or {}
    if union.get("union_id"):
        eid = "union"
        allowed.add(eid)
        evidence.append({"evidence_id": eid, "kind": "shortlist_union", "payload": {"union_id": union["union_id"]}})

    with conn.cursor() as cur:
        cur.execute(
            "select ticker, company_id::text from securities where security_id=%s::uuid",
            (security_id,),
        )
        row = cur.fetchone()
        ticker = row[0] if row else None
        company_id = row[1] if row else None

        cur.execute(
            """
            select item_ref, payload from snapshot_items
            where snapshot_id=%s::uuid and item_type='daily_price'
              and payload->>'security_id'=%s
            order by payload->>'trading_date' desc
            limit %s
            """,
            (snapshot_id, security_id, max_prices),
        )
        prices = []
        for item_ref, payload in cur.fetchall():
            pl = payload if isinstance(payload, dict) else json.loads(payload)
            eid = f"price:{item_ref}"
            allowed.add(eid)
            evidence.append(
                {
                    "evidence_id": eid,
                    "kind": "daily_price",
                    "ref": item_ref,
                    "trading_date": pl.get("trading_date"),
                    "close": pl.get("close"),
                }
            )
            prices.append(
                {
                    "trading_date": pl.get("trading_date"),
                    "close": pl.get("close"),
                    "evidence_id": eid,
                }
            )

        facts: list[dict[str, Any]] = []
        filings: list[dict[str, Any]] = []
        if company_id:
            cur.execute(
                """
                select item_ref, payload from snapshot_items
                where snapshot_id=%s::uuid and item_type='financial_fact'
                  and payload->>'company_id'=%s
                order by payload->>'period_end' desc
                limit %s
                """,
                (snapshot_id, company_id, max_facts),
            )
            for item_ref, payload in cur.fetchall():
                pl = payload if isinstance(payload, dict) else json.loads(payload)
                eid = f"fact:{item_ref}"
                allowed.add(eid)
                item = {
                    "evidence_id": eid,
                    "kind": "financial_fact",
                    "ref": item_ref,
                    "metric_key": pl.get("metric_key"),
                    "value": pl.get("value"),
                    "period_end": pl.get("period_end"),
                    "published_at": pl.get("published_at"),
                    "source_id": pl.get("source_id"),
                }
                evidence.append(item)
                facts.append(item)
                # Treat SEC-sourced facts as event/filing evidence
                if pl.get("source_id") or pl.get("published_at"):
                    feid = f"filing:{item_ref}"
                    allowed.add(feid)
                    filings.append({**item, "evidence_id": feid, "kind": "filing_or_fact"})
                    evidence.append({"evidence_id": feid, "kind": "filing_or_fact", "payload": pl})

        # Quant score if present for run
        cur.execute(
            """
            select total_score, growth_score, quality_score, valuation_score, momentum_score, rank_market
            from quant_scores
            where security_id=%s::uuid
            order by run_id desc
            limit 1
            """,
            (security_id,),
        )
        q = cur.fetchone()
        quant = None
        if q:
            eid = "quant"
            allowed.add(eid)
            quant = {
                "total_score": float(q[0]) if q[0] is not None else None,
                "growth_score": float(q[1]) if q[1] is not None else None,
                "quality_score": float(q[2]) if q[2] is not None else None,
                "valuation_score": float(q[3]) if q[3] is not None else None,
                "momentum_score": float(q[4]) if q[4] is not None else None,
                "rank_market": q[5],
                "evidence_id": eid,
            }
            evidence.append({"evidence_id": eid, "kind": "quant_score", "payload": quant})

    return {
        "security_id": security_id,
        "ticker": ticker,
        "allowed_evidence_ids": sorted(allowed),
        "evidence": evidence,
        "prices": prices,
        "financial_facts": facts,
        "filings_or_events": filings,
        "quant": quant,
    }


def validate_research_evidence_ids(
    research_output: dict[str, Any],
    allowed_evidence_ids: set[str] | list[str],
) -> tuple[str, list[str]]:
    """Deterministic gate: unknown evidence IDs fail before LLM QA trust."""
    allowed = set(allowed_evidence_ids)
    failed: list[str] = []
    for claim in research_output.get("claims") or []:
        if not isinstance(claim, dict):
            failed.append("malformed_claim")
            continue
        eid = claim.get("evidence_id")
        if not eid or eid not in allowed:
            failed.append(f"unknown_evidence:{eid}")
    for ref in research_output.get("evidence_refs") or []:
        if ref not in allowed:
            failed.append(f"unknown_ref:{ref}")
    if failed:
        return "FAIL", failed
    return "PASS", []
