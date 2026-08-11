from __future__ import annotations

from typing import Any

import psycopg
from fastapi import APIRouter, HTTPException, Query

from app.settings import get_settings

router = APIRouter(prefix="/v1", tags=["reads"])


def _conn():
    s = get_settings()
    if not s.supabase_db_url:
        raise HTTPException(status_code=503, detail="SUPABASE_DB_URL missing")
    return psycopg.connect(s.supabase_db_url)


@router.get("/dashboard")
def dashboard() -> dict[str, Any]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select run_id::text, status, cutoff_at::text, quant_rule_version,
                       llm_profile_version, code_commit_hash, created_at::text
                from research_runs
                order by created_at desc
                limit 1
                """
            )
            latest = cur.fetchone()
            cur.execute("select count(*) from securities")
            universe = cur.fetchone()[0]
            cur.execute("select count(*) from universe_memberships where included=true")
            eligible = cur.fetchone()[0]
            counts = {"SELECTED": 0, "WATCH": 0, "REJECT": 0}
            shortlist = 0
            qa_fail = 0
            if latest:
                run_id = latest[0]
                cur.execute("select count(*) from quant_scores where run_id=%s", (run_id,))
                shortlist = cur.fetchone()[0]
                cur.execute(
                    "select status, count(*) from judgments where run_id=%s group by status",
                    (run_id,),
                )
                for st, n in cur.fetchall():
                    counts[st] = n
                cur.execute(
                    """
                    select count(*) from research_qa q
                    join ai_research r on r.research_id=q.research_id
                    where r.run_id=%s and q.status='FAIL'
                    """,
                    (run_id,),
                )
                qa_fail = cur.fetchone()[0]
            cur.execute("select count(*) from data_quarantine")
            quarantine = cur.fetchone()[0]
    return {
        "latest_run": (
            {
                "run_id": latest[0],
                "status": latest[1],
                "cutoff_at": latest[2],
                "quant_rule_version": latest[3],
                "llm_profile_version": latest[4],
                "code_commit_hash": latest[5],
                "created_at": latest[6],
            }
            if latest
            else None
        ),
        "counts": {
            "universe": universe,
            "eligible": eligible,
            "shortlist": shortlist,
            "selected": counts.get("SELECTED", 0),
            "watch": counts.get("WATCH", 0),
            "reject": counts.get("REJECT", 0),
            "research_qa_fail": qa_fail,
            "quarantine": quarantine,
        },
    }


@router.get("/runs")
def list_runs(limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select r.run_id::text, r.status, r.cutoff_at::text, r.quant_rule_version,
                       r.prompt_bundle_version, r.llm_profile_version, r.code_commit_hash,
                       r.created_at::text,
                       (select count(*) from quant_scores q where q.run_id=r.run_id) as candidates,
                       (select count(*) from judgments j where j.run_id=r.run_id and j.status='SELECTED') as selected
                from research_runs r
                order by r.created_at desc
                limit %s
                """,
                (limit,),
            )
            rows = [
                {
                    "run_id": r[0],
                    "status": r[1],
                    "cutoff_at": r[2],
                    "quant_rule_version": r[3],
                    "prompt_bundle_version": r[4],
                    "llm_profile_version": r[5],
                    "code_commit_hash": r[6],
                    "created_at": r[7],
                    "candidates": r[8],
                    "selected": r[9],
                }
                for r in cur.fetchall()
            ]
    return {"runs": rows}


@router.get("/runs/{run_id}")
def run_detail(run_id: str) -> dict[str, Any]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select run_id::text, status, cutoff_at::text, quant_rule_version,
                       prompt_bundle_version, llm_profile_version, code_commit_hash,
                       universe_rule_version, created_at::text
                from research_runs where run_id=%s
                """,
                (run_id,),
            )
            r = cur.fetchone()
            if not r:
                raise HTTPException(status_code=404, detail="run not found")
            cur.execute(
                """
                select snapshot_id::text, content_hash, cutoff_at::text, created_at::text
                from snapshots where run_id=%s
                """,
                (run_id,),
            )
            snap = cur.fetchone()
            cur.execute(
                """
                select execution_id::text, agent_role, requested_model, resolved_model,
                       reasoning_effort, status, input_hash, output_hash, error_code, llm_profile_version
                from llm_executions where run_id=%s
                order by started_at
                """,
                (run_id,),
            )
            execs = [
                {
                    "execution_id": e[0],
                    "agent_role": e[1],
                    "requested_model": e[2],
                    "resolved_model": e[3],
                    "reasoning_effort": e[4],
                    "status": e[5],
                    "input_hash": e[6],
                    "output_hash": e[7],
                    "error_code": e[8],
                    "llm_profile_version": e[9],
                }
                for e in cur.fetchall()
            ]
    return {
        "run": {
            "run_id": r[0],
            "status": r[1],
            "cutoff_at": r[2],
            "quant_rule_version": r[3],
            "prompt_bundle_version": r[4],
            "llm_profile_version": r[5],
            "code_commit_hash": r[6],
            "universe_rule_version": r[7],
            "created_at": r[8],
        },
        "snapshot": (
            {
                "snapshot_id": snap[0],
                "content_hash": snap[1],
                "cutoff_at": snap[2],
                "created_at": snap[3],
            }
            if snap
            else None
        ),
        "llm_executions": execs,
    }


@router.get("/runs/{run_id}/candidates")
def candidates(run_id: str) -> dict[str, Any]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select q.security_id::text, s.ticker, s.exchange, q.rank_market, q.total_score,
                       q.growth_score, q.quality_score, q.cashflow_score, q.health_score,
                       q.valuation_score, q.momentum_score, q.rule_version,
                       j.status as final_status,
                       qa.status as research_qa
                from quant_scores q
                join securities s on s.security_id=q.security_id
                left join judgments j on j.run_id=q.run_id and j.security_id=q.security_id
                left join lateral (
                  select rq.status
                  from ai_research ar
                  join research_qa rq on rq.research_id=ar.research_id
                  where ar.run_id=q.run_id and ar.security_id=q.security_id
                  order by rq.created_at desc
                  limit 1
                ) qa on true
                where q.run_id=%s
                order by q.rank_market nulls last, s.ticker
                """,
                (run_id,),
            )
            rows = [
                {
                    "security_id": r[0],
                    "ticker": r[1],
                    "exchange": r[2],
                    "rank": r[3],
                    "total_score": float(r[4]),
                    "components": {
                        "growth": float(r[5]),
                        "quality": float(r[6]),
                        "cashflow": float(r[7]),
                        "health": float(r[8]),
                        "valuation": float(r[9]),
                        "momentum": float(r[10]),
                    },
                    "rule_version": r[11],
                    "final_status": r[12],
                    "research_qa": r[13],
                }
                for r in cur.fetchall()
            ]
    return {"run_id": run_id, "candidates": rows}


@router.get("/companies/{security_id}")
def company_detail(security_id: str, run_id: str = Query(...)) -> dict[str, Any]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select s.security_id::text, s.ticker, s.exchange, s.company_id::text, c.legal_name
                from securities s
                left join companies c on c.company_id=s.company_id
                where s.security_id=%s
                """,
                (security_id,),
            )
            srow = cur.fetchone()
            if not srow:
                raise HTTPException(status_code=404, detail="security not found")
            cur.execute(
                """
                select total_score, growth_score, quality_score, cashflow_score, health_score,
                       valuation_score, momentum_score, rank_market, rule_version, input_hash
                from quant_scores where run_id=%s and security_id=%s
                """,
                (run_id, security_id),
            )
            q = cur.fetchone()
            cur.execute(
                """
                select status, thesis, bear_case, risks, invalidation_conditions,
                       evidence_quality, data_completeness, uncertainty, selection_price,
                       immutable_hash, created_at::text
                from judgments where run_id=%s and security_id=%s
                order by created_at desc limit 1
                """,
                (run_id, security_id),
            )
            j = cur.fetchone()
            cur.execute(
                """
                select ar.output_json, rq.status, rq.failed_claims, rq.warnings
                from ai_research ar
                left join research_qa rq on rq.research_id=ar.research_id
                where ar.run_id=%s and ar.security_id=%s
                order by ar.created_at desc limit 1
                """,
                (run_id, security_id),
            )
            research = cur.fetchone()
            cur.execute(
                """
                select rp.payload_json->'evidence' as evidence,
                       rp.payload_json->'price_metrics' as price_metrics,
                       rp.payload_json->'financial_trends' as financial_trends,
                       rp.input_hash
                from research_packets rp
                where rp.run_id=%s and rp.security_id=%s
                order by rp.created_at desc limit 1
                """,
                (run_id, security_id),
            )
            packet = cur.fetchone()
    return {
        "identity": {
            "security_id": srow[0],
            "ticker": srow[1],
            "exchange": srow[2],
            "company_id": srow[3],
            "name": srow[4],
        },
        "run_id": run_id,
        "quant": (
            {
                "total_score": float(q[0]),
                "components": {
                    "growth": float(q[1]),
                    "quality": float(q[2]),
                    "cashflow": float(q[3]),
                    "health": float(q[4]),
                    "valuation": float(q[5]),
                    "momentum": float(q[6]),
                },
                "rank_market": q[7],
                "rule_version": q[8],
                "input_hash": q[9],
            }
            if q
            else None
        ),
        "judgment": (
            {
                "status": j[0],
                "thesis": j[1],
                "bear_case": j[2],
                "risks": j[3],
                "invalidation_conditions": j[4],
                "evidence_quality": j[5],
                "data_completeness": float(j[6]),
                "uncertainty": j[7],
                "selection_price": float(j[8]) if j[8] is not None else None,
                "immutable_hash": j[9],
                "created_at": j[10],
            }
            if j
            else None
        ),
        "research": (
            {
                "output": research[0],
                "qa_status": research[1],
                "failed_claims": research[2],
                "warnings": research[3],
            }
            if research
            else None
        ),
        "packet": (
            {
                "evidence": packet[0],
                "price_metrics": packet[1],
                "financial_trends": packet[2],
                "input_hash": packet[3],
            }
            if packet
            else None
        ),
    }


@router.get("/audit/summary")
def audit_summary() -> dict[str, Any]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select status, count(*) from research_qa group by status
                """
            )
            qa = {r[0]: r[1] for r in cur.fetchall()}
            cur.execute(
                """
                select agent_role, status, count(*) from llm_executions group by 1,2 order by 1,2
                """
            )
            execs = [{"agent_role": r[0], "status": r[1], "count": r[2]} for r in cur.fetchall()]
            cur.execute("select count(*) from data_quarantine")
            quarantine = cur.fetchone()[0]
            cur.execute(
                """
                select check_name, status, details
                from data_quality_checks
                order by ran_at desc
                limit 20
                """
            )
            checks = [
                {"check_name": r[0], "status": r[1], "details": r[2]} for r in cur.fetchall()
            ]
    return {"research_qa": qa, "llm_executions": execs, "quarantine": quarantine, "recent_checks": checks}


@router.get("/settings/summary")
def settings_summary() -> dict[str, Any]:
    from app.config_registry import list_config_versions
    from app.llm_profiles import load_llm_profiles, profiles_as_dict

    s = get_settings()
    profiles = load_llm_profiles()
    return {
        "llm_profile_version": profiles.version,
        "llm_profiles": profiles_as_dict(profiles),
        "registry": list_config_versions(),
        "providers": {
            "supabase_url_set": bool(s.supabase_url),
            "supabase_db_set": bool(s.supabase_db_url),
            "openai_key_set": bool(s.openai_api_key),
            "massive_key_set": bool(s.massive_api_key),
            "sec_ua_set": bool(s.sec_user_agent),
            "fred_key_set": bool(s.fred_api_key),
            # never return raw secrets
        },
    }


@router.get("/ops/health")
def ops_health() -> dict[str, Any]:
    """Operational health for M1 — job ledger + readiness flags (no secrets)."""
    import json
    from pathlib import Path

    from app.ops.jobs import list_recent_jobs

    s = get_settings()
    evidence = (
        Path(__file__).resolve().parents[3]
        / "audit"
        / "post-mvp"
        / "M01_automation_deployment"
        / "evidence"
        / "backup_readiness.json"
    )
    backup_ready = False
    if evidence.is_file():
        try:
            payload = json.loads(evidence.read_text(encoding="utf-8"))
            backup_ready = bool(payload.get("ok"))
        except Exception:  # noqa: BLE001
            backup_ready = False
    jobs: list[dict[str, Any]] = []
    failed_24h = 0
    if s.supabase_db_url:
        with _conn() as conn:
            jobs = list_recent_jobs(conn, limit=20)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select count(*) from ops_jobs
                    where status in ('failed', 'dead_letter')
                      and started_at > now() - interval '24 hours'
                    """
                )
                failed_24h = int(cur.fetchone()[0])
    return {
        "status": "ok",
        "pitr_available": False,
        "pitr_confirmed": False,
        "backup_ready": backup_ready,
        "scheduler_enable_allowed": False,
        "failed_jobs_24h": failed_24h,
        "recent_jobs": jobs,
        "providers": {
            "supabase_db_set": bool(s.supabase_db_url),
            "openai_key_set": bool(s.openai_api_key),
            "massive_key_set": bool(s.massive_api_key),
            "sec_ua_set": bool(s.sec_user_agent),
            "fred_key_set": bool(s.fred_api_key),
        },
    }


@router.get("/topdown/summary")
def topdown_summary() -> dict[str, Any]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select regime_id::text, as_of::text, regime, rule_version
                from market_regimes
                order by created_at desc
                limit 1
                """
            )
            regime = cur.fetchone()
            cur.execute(
                """
                select industry_id, overall_score, as_of::text
                from industry_assessments
                order by created_at desc
                limit 10
                """
            )
            assessments = [
                {"industry_id": r[0], "overall_score": float(r[1]), "as_of": r[2]} for r in cur.fetchall()
            ]
            cur.execute(
                """
                select union_id::text, as_of::text, jsonb_array_length(members)
                from shortlist_unions
                order by created_at desc
                limit 1
                """
            )
            union = cur.fetchone()
    return {
        "latest_regime": (
            {
                "regime_id": regime[0],
                "as_of": regime[1],
                "regime": regime[2],
                "rule_version": regime[3],
            }
            if regime
            else None
        ),
        "recent_assessments": assessments,
        "latest_union": (
            {"union_id": union[0], "as_of": union[1], "member_count": union[2]} if union else None
        ),
        "scheduler_enable_allowed": False,
    }


@router.get("/performance/summary")
def performance_summary() -> dict[str, Any]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select horizon, status, count(*)
                from performance_evals
                group by horizon, status
                order by horizon, status
                """
            )
            counts = [{"horizon": r[0], "status": r[1], "n": int(r[2])} for r in cur.fetchall()]
            cur.execute(
                """
                select cohort, horizon, avg(abs_return)
                from performance_evals
                where status='COMPLETE' and abs_return is not null
                group by cohort, horizon
                order by cohort, horizon
                """
            )
            avgs = [
                {
                    "cohort": r[0],
                    "horizon": r[1],
                    "avg_abs_return": float(r[2]) if r[2] is not None else None,
                }
                for r in cur.fetchall()
            ]
    return {"counts": counts, "avg_abs_by_cohort": avgs, "scheduler_enable_allowed": False}
