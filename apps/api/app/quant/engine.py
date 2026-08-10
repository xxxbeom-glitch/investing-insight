from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date
from typing import Any

import psycopg

from app.quant.config import QuantRules, load_quant_rules
from app.quant.metrics import (
    cashflow_proxy,
    growth_from_revenues,
    health_from_equity_ratio,
    momentum_from_closes,
    quality_from_roe,
    valuation_from_price_to_book,
    weighted_total,
)


def _input_hash(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _latest_two(values: list[tuple[date, float]]) -> tuple[float | None, float | None]:
    ordered = sorted(values, key=lambda x: x[0], reverse=True)
    latest = ordered[0][1] if ordered else None
    prior = ordered[1][1] if len(ordered) > 1 else None
    return latest, prior


def score_security(
    *,
    facts_by_metric: dict[str, list[tuple[date, float]]],
    closes: list[tuple[date, float]],
    rules: QuantRules,
) -> dict[str, Any]:
    rev_l, rev_p = _latest_two(facts_by_metric.get("Revenues", []))
    ni_l, _ = _latest_two(facts_by_metric.get("NetIncomeLoss", []))
    eq_l, _ = _latest_two(facts_by_metric.get("StockholdersEquity", []))
    as_l, _ = _latest_two(facts_by_metric.get("Assets", []))
    close_series = [c for _, c in sorted(closes, key=lambda x: x[0])]
    close_l = close_series[-1] if close_series else None

    growth, g_miss = growth_from_revenues(rev_l, rev_p, neutral=rules.neutral_score)
    quality, q_miss = quality_from_roe(ni_l, eq_l, neutral=rules.neutral_score)
    cashflow, c_miss = cashflow_proxy(ni_l, as_l, neutral=rules.neutral_score)
    health, h_miss = health_from_equity_ratio(eq_l, as_l, neutral=rules.neutral_score)
    valuation, v_miss = valuation_from_price_to_book(close_l, eq_l, neutral=rules.neutral_score)
    momentum, m_miss = momentum_from_closes(close_series, neutral=rules.neutral_score)

    components = {
        "growth": growth,
        "quality": quality,
        "cashflow": cashflow,
        "health": health,
        "valuation": valuation,
        "momentum": momentum,
    }
    missing = [
        name
        for name, miss in (
            ("growth", g_miss),
            ("quality", q_miss),
            ("cashflow", c_miss),
            ("health", h_miss),
            ("valuation", v_miss),
            ("momentum", m_miss),
        )
        if miss
    ]
    total = weighted_total(components, rules.weights)
    ih = _input_hash(
        {
            "facts": {k: [[d.isoformat(), v] for d, v in sorted(vs)] for k, vs in sorted(facts_by_metric.items())},
            "closes": [[d.isoformat(), v] for d, v in sorted(closes)],
            "rule_version": rules.version,
            "weights": rules.weights,
        }
    )
    return {
        **{f"{k}_score": v for k, v in components.items()},
        "total_score": total,
        "missing_components": missing,
        "input_hash": ih,
        "rule_version": rules.version,
    }


def run_quant_for_snapshot(
    conn: psycopg.Connection,
    *,
    snapshot_id: str,
    run_id: str,
    rules: QuantRules | None = None,
) -> dict[str, Any]:
    rules = rules or load_quant_rules()
    with conn.cursor() as cur:
        cur.execute(
            """
            select item_ref, payload
            from snapshot_items
            where snapshot_id=%s and item_type='universe_membership'
            """,
            (snapshot_id,),
        )
        memberships = cur.fetchall()
        included: list[str] = []
        for sid, payload in memberships:
            if payload.get("included") is True:
                included.append(sid)
        if not included:
            return {"scored": 0, "shortlist": []}

        cur.execute(
            """
            select item_ref, payload
            from snapshot_items
            where snapshot_id=%s and item_type='daily_price'
            """,
            (snapshot_id,),
        )
        closes_by_sid: dict[str, list[tuple[date, float]]] = defaultdict(list)
        for _, payload in cur.fetchall():
            sid = payload["security_id"]
            closes_by_sid[sid].append((date.fromisoformat(payload["trading_date"]), float(payload["close"])))

        cur.execute(
            """
            select s.security_id::text, s.company_id::text
            from securities s
            where s.security_id = any(%s::uuid[])
            """,
            (included,),
        )
        company_of = {sid: cid for sid, cid in cur.fetchall()}

        cur.execute(
            """
            select payload
            from snapshot_items
            where snapshot_id=%s and item_type='financial_fact'
            """,
            (snapshot_id,),
        )
        facts_by_company: dict[str, dict[str, list[tuple[date, float]]]] = defaultdict(lambda: defaultdict(list))
        for (payload,) in cur.fetchall():
            cid = payload["company_id"]
            pe = payload.get("period_end")
            if not pe:
                continue
            facts_by_company[cid][payload["metric_key"]].append(
                (date.fromisoformat(pe), float(payload["value"]))
            )

        rows: list[dict[str, Any]] = []
        for sid in included:
            cid = company_of.get(sid)
            facts = facts_by_company.get(cid or "", {})
            scored = score_security(facts_by_metric=facts, closes=closes_by_sid.get(sid, []), rules=rules)
            rows.append({"security_id": sid, **scored})

        rows.sort(key=lambda r: (-r["total_score"], r["security_id"]))
        for i, r in enumerate(rows, start=1):
            r["rank_market"] = i
            r["rank_peer"] = i
            r["peer_group"] = "market"

        cur.execute("delete from quant_scores where run_id=%s", (run_id,))
        for r in rows:
            cur.execute(
                """
                insert into quant_scores (
                  run_id, security_id, total_score, growth_score, quality_score, cashflow_score,
                  health_score, valuation_score, momentum_score, peer_group, rank_market, rank_peer,
                  rule_version, input_hash, missing_components
                ) values (
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb
                )
                """,
                (
                    run_id,
                    r["security_id"],
                    r["total_score"],
                    r["growth_score"],
                    r["quality_score"],
                    r["cashflow_score"],
                    r["health_score"],
                    r["valuation_score"],
                    r["momentum_score"],
                    r["peer_group"],
                    r["rank_market"],
                    r["rank_peer"],
                    r["rule_version"],
                    r["input_hash"],
                    json.dumps(r["missing_components"]),
                ),
            )
        cur.execute(
            "update research_runs set status='quant_ready', quant_rule_version=%s where run_id=%s",
            (rules.version, run_id),
        )
    conn.commit()
    shortlist = [r["security_id"] for r in rows[: rules.shortlist_size]]
    return {"scored": len(rows), "shortlist": shortlist, "rule_version": rules.version}
