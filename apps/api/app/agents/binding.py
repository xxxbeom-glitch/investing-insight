from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg

from app.snapshot.engine import create_snapshot


def context_hash(frozen: dict[str, Any]) -> str:
    blob = json.dumps(frozen, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


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
            select union_id::text, as_of::text, bottom_up_run_id::text, members
            from shortlist_unions
            order by created_at desc
            limit 1
            """
        )
        row = cur.fetchone()
        if row:
            ctx["union"] = {
                "union_id": row[0],
                "as_of": row[1],
                "bottom_up_run_id": row[2],
                "members": row[3] if isinstance(row[3], list) else json.loads(row[3] or "[]"),
            }
        cur.execute(
            """
            select regime_id::text, as_of::text, regime, inputs, rule_version
            from market_regimes
            order by created_at desc
            limit 1
            """
        )
        row = cur.fetchone()
        if row:
            inputs = row[3] if isinstance(row[3], dict) else json.loads(row[3] or "{}")
            ctx["regime"] = {
                "regime_id": row[0],
                "as_of": row[1],
                "regime": row[2],
                "inputs": inputs,
                "rule_version": row[4],
            }
        cur.execute(
            """
            select distinct on (industry_id)
              assessment_id::text, industry_id, overall_score, as_of::text, details
            from industry_assessments
            order by industry_id, created_at desc
            """
        )
        for aid, industry_id, overall, as_of, details in cur.fetchall():
            det = details if isinstance(details, dict) else json.loads(details or "{}")
            ctx["assessments"].append(
                {
                    "assessment_id": aid,
                    "industry_id": industry_id,
                    "overall_score": float(overall),
                    "as_of": as_of,
                    "details": det,
                }
            )
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


class FrozenContextError(RuntimeError):
    pass


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
