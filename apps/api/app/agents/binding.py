from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg

from app.snapshot.engine import create_snapshot


class FrozenContextError(RuntimeError):
    pass


def context_hash(frozen: dict[str, Any]) -> str:
    blob = json.dumps(frozen, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def bind_union_lineage(
    union: dict[str, Any],
    assessments: list[dict[str, Any]],
    regimes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Bind exact union assessment IDs and their shared regime — never latest-by-created_at."""
    raw_ids = list(union.get("topdown_assessment_ids") or [])
    ids = [str(x) for x in raw_ids if str(x).strip()]
    if not ids:
        raise FrozenContextError("union missing topdown_assessment_ids")
    if len(ids) != len(set(ids)):
        raise FrozenContextError("duplicate assessment ids in union")
    by_id = {str(a.get("assessment_id")): a for a in assessments}
    ordered: list[dict[str, Any]] = []
    for aid in ids:
        row = by_id.get(aid)
        if not row:
            raise FrozenContextError(f"assessment missing: {aid}")
        ordered.append(row)
    regime_ids = {str(a.get("regime_id") or "") for a in ordered}
    if "" in regime_ids or len(regime_ids) != 1:
        raise FrozenContextError("assessments span inconsistent regime lineage")
    rid = next(iter(regime_ids))
    regime = next((r for r in regimes if str(r.get("regime_id")) == rid), None)
    if not regime:
        raise FrozenContextError(f"regime missing: {rid}")
    as_ofs = {str(a.get("as_of") or "") for a in ordered}
    if "" in as_ofs or len(as_ofs) != 1:
        raise FrozenContextError("assessments span inconsistent as_of lineage")
    if str(regime.get("as_of") or "") not in as_ofs:
        raise FrozenContextError("regime as_of diverges from assessments")
    return {
        "assessments": ordered,
        "regime": regime,
        "topdown_assessment_ids": ids,
        "regime_id": rid,
    }


def _load_frozen_context(conn: psycopg.Connection) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "union": None,
        "regime": None,
        "assessments": [],
        "bottom_up": None,
    }
    with conn.cursor() as cur:
        cur.execute(
            """
            select union_id::text, as_of::text, bottom_up_run_id::text, members, topdown_assessment_ids
            from shortlist_unions
            order by created_at desc
            limit 1
            """
        )
        row = cur.fetchone()
        if not row:
            return ctx
        ids = row[4] or []
        if hasattr(ids, "tolist"):
            ids = list(ids)
        elif not isinstance(ids, list):
            ids = list(ids)
        ctx["union"] = {
            "union_id": row[0],
            "as_of": row[1],
            "bottom_up_run_id": row[2],
            "members": row[3] if isinstance(row[3], list) else json.loads(row[3] or "[]"),
            "topdown_assessment_ids": [str(x) for x in ids],
        }
        cur.execute(
            """
            select assessment_id::text, industry_id, overall_score, as_of::text, details,
                   regime_id::text
            from industry_assessments
            where assessment_id = any(%s::uuid[])
            """,
            (ctx["union"]["topdown_assessment_ids"],),
        )
        assessments = []
        for aid, industry_id, overall, as_of, details, regime_id in cur.fetchall():
            det = details if isinstance(details, dict) else json.loads(details or "{}")
            assessments.append(
                {
                    "assessment_id": aid,
                    "industry_id": industry_id,
                    "overall_score": float(overall),
                    "as_of": as_of,
                    "details": det,
                    "regime_id": regime_id,
                }
            )
        regime_ids = sorted({a["regime_id"] for a in assessments if a.get("regime_id")})
        regimes: list[dict[str, Any]] = []
        if regime_ids:
            cur.execute(
                """
                select regime_id::text, as_of::text, regime, inputs, rule_version
                from market_regimes
                where regime_id = any(%s::uuid[])
                """,
                (regime_ids,),
            )
            for rid, as_of, regime, inputs, rule_version in cur.fetchall():
                inp = inputs if isinstance(inputs, dict) else json.loads(inputs or "{}")
                regimes.append(
                    {
                        "regime_id": rid,
                        "as_of": as_of,
                        "regime": regime,
                        "inputs": inp,
                        "rule_version": rule_version,
                    }
                )
        bound = bind_union_lineage(ctx["union"], assessments, regimes)
        ctx["assessments"] = bound["assessments"]
        ctx["regime"] = bound["regime"]
        ctx["union"]["topdown_assessment_ids"] = bound["topdown_assessment_ids"]
        ctx["lineage"] = {
            "topdown_assessment_ids": bound["topdown_assessment_ids"],
            "regime_id": bound["regime_id"],
            "assessment_as_of": [a.get("as_of") for a in bound["assessments"]],
            "regime_as_of": bound["regime"].get("as_of"),
        }
        bottom_run = (ctx["union"] or {}).get("bottom_up_run_id")
        if bottom_run:
            cur.execute(
                """
                select s.ticker, q.security_id::text, q.total_score, q.rank_market
                from quant_scores q
                join securities s on s.security_id = q.security_id
                where q.run_id = %s::uuid
                order by q.rank_market nulls last, q.total_score desc
                limit 30
                """,
                (bottom_run,),
            )
            ctx["bottom_up"] = {
                "run_id": bottom_run,
                "shortlist": [
                    {
                        "ticker": t,
                        "security_id": sid,
                        "total_score": float(score),
                        "rank_market": rank,
                    }
                    for t, sid, score, rank in cur.fetchall()
                ],
            }
    return ctx


def verify_frozen_context(conn: psycopg.Connection, multi_agent_run_id: str) -> dict[str, Any]:
    """Reload frozen_context from DB and fail-closed if hash diverges (ER2-P0-01)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            select frozen_context, context_hash, snapshot_id::text, run_id::text
            from multi_agent_runs
            where multi_agent_run_id=%s::uuid
            """,
            (multi_agent_run_id,),
        )
        row = cur.fetchone()
    if not row:
        raise FrozenContextError(f"multi_agent_run not found: {multi_agent_run_id}")
    frozen = row[0] if isinstance(row[0], dict) else json.loads(row[0] or "{}")
    stored = row[1]
    recomputed = context_hash(frozen)
    if not stored or stored != recomputed:
        raise FrozenContextError("context_hash mismatch — frozen_context tampered or stale")
    return frozen


def attach_quant_records(
    conn: psycopg.Connection,
    frozen: dict[str, Any],
    security_ids: list[str],
) -> dict[str, Any]:
    """Bind Quant to frozen bottom_up_run_id only — never borrow another run (ER2-P1-01)."""
    from app.agents.evidence import load_quant_for_frozen_run

    run_id = (frozen.get("bottom_up") or {}).get("run_id") or (frozen.get("union") or {}).get(
        "bottom_up_run_id"
    )
    records = []
    for sid in security_ids:
        rec = load_quant_for_frozen_run(conn, security_id=sid, frozen_run_id=run_id)
        if rec:
            records.append(rec)
    frozen["quant_records"] = records
    frozen["quant_run_id"] = run_id
    return frozen


def bind_multi_agent_run(
    conn: psycopg.Connection,
    *,
    code_commit_hash: str = "m03-multi-agent",
    llm_profile_version: str = "llm-profile-v0.2",
    security_limit: int = 1,
) -> dict[str, Any]:
    """Freeze top-down/bottom-up context and create a shared Snapshot for all agents.

    Multi-agent context lives on multi_agent_runs.context_hash / frozen_context —
    never post-hash into snapshot_items (ER-P0-01).
    """
    frozen = _load_frozen_context(conn)
    if not frozen.get("union"):
        raise RuntimeError("no shortlist_unions — run topdown slice first")
    if not frozen.get("regime"):
        raise RuntimeError("no market_regimes — run topdown slice first")

    members = frozen["union"]["members"] or []
    security_ids = [m["security_id"] for m in members if m.get("security_id")][:security_limit]
    if not security_ids:
        with conn.cursor() as cur:
            cur.execute(
                """
                select distinct dp.security_id::text
                from daily_prices dp
                order by dp.security_id
                limit %s
                """,
                (security_limit,),
            )
            security_ids = [r[0] for r in cur.fetchall()]
    if not security_ids:
        raise RuntimeError("no securities for multi-agent snapshot")

    snap = create_snapshot(
        conn,
        cutoff_at=datetime.now(timezone.utc),
        code_commit_hash=code_commit_hash,
        llm_profile_version=llm_profile_version,
        security_ids=security_ids,
    )
    frozen["snapshot_content_hash"] = snap["content_hash"]
    frozen["snapshot_id"] = snap["snapshot_id"]
    attach_quant_records(conn, frozen, security_ids)

    ctx_hash = context_hash(frozen)
    multi_id = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into multi_agent_runs (
              multi_agent_run_id, run_id, snapshot_id, union_id, bottom_up_run_id, regime_id,
              llm_profile_version, frozen_context, context_hash, status
            ) values (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,'running')
            """,
            (
                multi_id,
                snap["run_id"],
                snap["snapshot_id"],
                frozen["union"]["union_id"],
                (frozen.get("bottom_up") or {}).get("run_id"),
                frozen["regime"]["regime_id"],
                llm_profile_version,
                json.dumps(frozen),
                ctx_hash,
            ),
        )
    conn.commit()
    return {
        "multi_agent_run_id": multi_id,
        "run_id": snap["run_id"],
        "snapshot_id": snap["snapshot_id"],
        "content_hash": snap["content_hash"],
        "context_hash": ctx_hash,
        "security_ids": security_ids,
        "frozen_context": frozen,
    }
