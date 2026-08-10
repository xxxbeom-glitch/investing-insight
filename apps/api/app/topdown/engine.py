from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import psycopg
import yaml

from app.macro.regime import load_industry_rules

REPO_ROOT = Path(__file__).resolve().parents[4]
CHAIN_PATH = REPO_ROOT / "config" / "value_chain.v0.1.yaml"


def load_value_chain(path: Path | None = None) -> dict[str, Any]:
    return yaml.safe_load((path or CHAIN_PATH).read_text(encoding="utf-8")) or {}


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def score_industry(
    industry: dict[str, Any],
    latest: dict[str, dict[str, Any]],
    regime: str,
) -> dict[str, float]:
    """Deterministic 6-dimension scores from FRED tilts + regime."""
    base = {
        "demand": 50.0,
        "capex": 50.0,
        "supply": 50.0,
        "pricing": 50.0,
        "margin": 50.0,
        "bottleneck": 50.0,
    }
    # Regime nudges
    if regime == "expansion":
        base["demand"] += 10
        base["margin"] += 5
        base["capex"] += 5
    elif regime == "late_cycle":
        base["pricing"] += 8
        base["bottleneck"] += 10
        base["margin"] -= 5
    elif regime == "contraction":
        base["demand"] -= 15
        base["capex"] -= 10
        base["margin"] -= 10

    tilt = industry.get("fred_tilt") or {}
    for role, dim in tilt.items():
        obs = latest.get(role)
        if not obs:
            continue
        val = float(obs["value"])
        if role == "labor":
            # lower unemployment → better demand
            delta = _clamp(60 - val * 8, -20, 20)
        elif role == "inflation":
            delta = _clamp((val - 2.0) * 3, -15, 15)  # mild inflation ok for pricing power proxy
        elif role == "yield_curve":
            delta = _clamp(val * 10, -20, 20)
        elif role == "policy_rate":
            delta = _clamp(5 - val, -15, 15) * 3
        elif role == "industrial_production":
            delta = _clamp((val - 100) * 0.5, -20, 20)
        else:
            delta = 0.0
        if dim in base:
            base[dim] += delta

    scored = {k: round(_clamp(v), 2) for k, v in base.items()}
    weights = industry.get("weights") or {}
    overall = 0.0
    wsum = 0.0
    for k, w in weights.items():
        overall += scored[k] * float(w)
        wsum += float(w)
    scored["overall"] = round(overall / wsum if wsum else 0.0, 2)
    return scored


def run_industry_assessments(
    conn: psycopg.Connection,
    *,
    regime_id: str,
    regime: str,
    as_of: str,
    latest: dict[str, dict[str, Any]],
    rules: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rules = rules or load_industry_rules()
    version = str(rules.get("version") or "industry-rules-v0.1")
    out: list[dict[str, Any]] = []
    with conn.cursor() as cur:
        for ind in rules.get("industries") or []:
            scores = score_industry(ind, latest, regime)
            aid = str(uuid.uuid4())
            cur.execute(
                """
                insert into industry_assessments (
                  assessment_id, industry_id, as_of, regime_id,
                  demand_score, capex_score, supply_score, pricing_score,
                  margin_score, bottleneck_score, overall_score,
                  details, rule_version
                ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
                """,
                (
                    aid,
                    ind["industry_id"],
                    as_of,
                    regime_id,
                    scores["demand"],
                    scores["capex"],
                    scores["supply"],
                    scores["pricing"],
                    scores["margin"],
                    scores["bottleneck"],
                    scores["overall"],
                    json.dumps({"name": ind.get("name"), "scores": scores}),
                    version,
                ),
            )
            out.append({"assessment_id": aid, "industry_id": ind["industry_id"], "scores": scores})
    conn.commit()
    return out


def industry_qa(
    conn: psycopg.Connection,
    assessment: dict[str, Any],
    rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rules = rules or load_industry_rules()
    qa_cfg = rules.get("qa") or {}
    scores = assessment["scores"]
    reasons: list[str] = []
    if qa_cfg.get("require_all_dimensions"):
        for k in ("demand", "capex", "supply", "pricing", "margin", "bottleneck"):
            if k not in scores:
                reasons.append(f"missing_dimension:{k}")
    min_overall = float(qa_cfg.get("min_overall", 40))
    if scores.get("overall", 0) < min_overall:
        reasons.append(f"overall_below_{min_overall}")
    status = "FAIL" if reasons else "PASS"
    qa_id = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into industry_qa (qa_id, assessment_id, status, reasons, rule_version)
            values (%s,%s,%s,%s::jsonb,%s)
            """,
            (
                qa_id,
                assessment["assessment_id"],
                status,
                json.dumps(reasons),
                str(rules.get("version") or "industry-rules-v0.1"),
            ),
        )
    conn.commit()
    return {"qa_id": qa_id, "status": status, "reasons": reasons}


def snapshot_value_chains(conn: psycopg.Connection) -> list[dict[str, Any]]:
    chain = load_value_chain()
    version = str(chain.get("version") or "value-chain-v0.1")
    out = []
    with conn.cursor() as cur:
        for c in chain.get("chains") or []:
            sid = str(uuid.uuid4())
            cur.execute(
                """
                insert into value_chain_snapshots (snapshot_id, industry_id, config_version, nodes)
                values (%s,%s,%s,%s::jsonb)
                """,
                (sid, c["industry_id"], version, json.dumps(c.get("nodes") or [])),
            )
            out.append({"snapshot_id": sid, "industry_id": c["industry_id"], "nodes": c.get("nodes") or []})
    conn.commit()
    return out


def promote_topdown_candidates(
    conn: psycopg.Connection,
    *,
    assessment: dict[str, Any],
    qa_status: str,
    chain_nodes: list[dict[str, Any]],
    block_on_fail: bool = True,
) -> list[dict[str, Any]]:
    if block_on_fail and qa_status == "FAIL":
        return []
    created = []
    with conn.cursor() as cur:
        for node in chain_nodes:
            for ticker in node.get("tickers") or []:
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
                security_id = row[0] if row else None
                cid = str(uuid.uuid4())
                cur.execute(
                    """
                    insert into topdown_candidates (
                      candidate_id, assessment_id, industry_id, ticker, node_id, security_id, qa_status
                    ) values (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        cid,
                        assessment["assessment_id"],
                        assessment["industry_id"],
                        ticker.upper(),
                        node.get("node_id"),
                        security_id,
                        qa_status,
                    ),
                )
                created.append({"candidate_id": cid, "ticker": ticker.upper(), "security_id": security_id})
    conn.commit()
    return created


def union_shortlists(
    conn: psycopg.Connection,
    *,
    as_of: str,
    assessment_ids: list[str],
    bottom_up_run_id: str | None = None,
) -> dict[str, Any]:
    members: list[dict[str, Any]] = []
    seen: set[str] = set()
    with conn.cursor() as cur:
        if assessment_ids:
            cur.execute(
                """
                select ticker, security_id::text, industry_id, 'topdown' as source
                from topdown_candidates
                where assessment_id = any(%s)
                """,
                (assessment_ids,),
            )
            for ticker, sid, industry_id, source in cur.fetchall():
                key = sid or ticker
                if key in seen:
                    continue
                seen.add(key)
                members.append(
                    {
                        "ticker": ticker,
                        "security_id": sid,
                        "industry_id": industry_id,
                        "source": source,
                    }
                )
        if bottom_up_run_id:
            cur.execute(
                """
                select s.ticker, q.security_id::text
                from quant_scores q
                join securities s on s.security_id = q.security_id
                where q.run_id = %s::uuid
                order by q.rank_market nulls last, q.total_score desc
                limit 50
                """,
                (bottom_up_run_id,),
            )
            for ticker, sid in cur.fetchall():
                key = sid or ticker
                if key in seen:
                    # mark dual
                    for m in members:
                        if (m.get("security_id") or m.get("ticker")) == key:
                            m["source"] = "both"
                    continue
                seen.add(key)
                members.append({"ticker": ticker, "security_id": sid, "source": "bottom_up"})

    union_id = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into shortlist_unions (union_id, as_of, topdown_assessment_ids, bottom_up_run_id, members)
            values (%s,%s,%s,%s,%s::jsonb)
            """,
            (
                union_id,
                as_of,
                assessment_ids or [],
                bottom_up_run_id,
                json.dumps(members),
            ),
        )
    conn.commit()
    return {"union_id": union_id, "member_count": len(members), "members": members}
