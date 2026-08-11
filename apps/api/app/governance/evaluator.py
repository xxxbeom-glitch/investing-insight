"""Deterministic replay/holdout evaluator — produces recorded artifacts (ER2-P1-03)."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg

from app.macro.ingest import latest_by_role
from app.macro.regime import classify_regime, load_industry_rules
from app.topdown.engine import score_industry

EVALUATOR_VERSION = "governance-eval-v0.1"
DEFAULT_THRESHOLDS = {
    "score_min": 0.0,
    "score_max": 100.0,
    "replay_overall_abs_delta_max": 1.0,
    "holdout_min_sample": 1,
}


class EvaluatorError(RuntimeError):
    pass


def _hash(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _canonical_artifact(row: dict[str, Any]) -> dict[str, Any]:
    # generated_at excluded: Postgres timestamptz text form is not byte-stable vs isoformat
    keys = (
        "evaluation_id",
        "eval_kind",
        "evaluator_version",
        "artifact_type",
        "artifact_ref",
        "candidate_version",
        "dataset_id",
        "dataset_hash",
        "sample_count",
        "metrics",
        "baseline",
        "thresholds",
        "status",
    )
    return {k: row[k] for k in keys}


def _score_from_latest(latest: dict[str, dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    rules = load_industry_rules()
    classified = classify_regime(latest)
    scored = []
    for ind in rules.get("industries") or []:
        scores = score_industry(ind, latest, classified["regime"])
        scored.append({"industry_id": ind["industry_id"], "overall": scores["overall"], "scores": scores})
    return classified["regime"], scored


def _inflation_ok(latest: dict[str, dict[str, Any]]) -> bool:
    inf = latest.get("inflation") or {}
    if not inf:
        return True
    unit = (inf.get("value_unit") or "").lower()
    val = float(inf["value"])
    if unit and unit not in {"yoy_pct", "percent_yoy", "pc1"}:
        return False
    return val <= 50


def run_replay_evaluation(
    conn: psycopg.Connection,
    *,
    artifact_type: str,
    artifact_ref: str,
    candidate_version: str,
) -> dict[str, Any]:
    """Replay current industry scores vs last stored assessments (same as-of inputs)."""
    latest = latest_by_role(conn)
    if not latest:
        raise EvaluatorError("no macro_observations for replay")
    if not _inflation_ok(latest):
        raise EvaluatorError("inflation unit invalid for replay")

    regime, scored = _score_from_latest(latest)
    stored: dict[str, float] = {}
    with conn.cursor() as cur:
        cur.execute(
            """
            select distinct on (industry_id) industry_id, overall_score
            from industry_assessments
            order by industry_id, created_at desc
            """
        )
        for industry_id, overall in cur.fetchall():
            stored[industry_id] = float(overall)

    deltas = []
    fail = False
    for row in scored:
        overall = float(row["overall"])
        if overall < DEFAULT_THRESHOLDS["score_min"] or overall > DEFAULT_THRESHOLDS["score_max"]:
            fail = True
        base = stored.get(row["industry_id"])
        delta = None if base is None else abs(overall - base)
        deltas.append({"industry_id": row["industry_id"], "replay_overall": overall, "stored_overall": base, "abs_delta": delta})
        if delta is not None and delta > DEFAULT_THRESHOLDS["replay_overall_abs_delta_max"]:
            fail = True

    dataset = {"kind": "replay_macro_latest", "roles": sorted(latest.keys()), "regime": regime}
    return _persist(
        conn,
        eval_kind="replay",
        artifact_type=artifact_type,
        artifact_ref=artifact_ref,
        candidate_version=candidate_version,
        dataset_id="macro-latest-replay",
        dataset_hash=_hash(dataset),
        sample_count=len(scored),
        metrics={"deltas": deltas, "regime": regime},
        baseline={"stored_overall": stored},
        status="FAIL" if fail else "PASS",
    )


def run_holdout_evaluation(
    conn: psycopg.Connection,
    *,
    artifact_type: str,
    artifact_ref: str,
    candidate_version: str,
) -> dict[str, Any]:
    """Holdout: score using the previous (non-latest) inflation observation date when available."""
    with conn.cursor() as cur:
        cur.execute(
            """
            select distinct on (role) role, series_id, observation_date::text, value, value_unit
            from macro_observations
            where role is not null and value is not null
            order by role, observation_date desc
            """
        )
        latest_rows = cur.fetchall()
        cur.execute(
            """
            select role, series_id, observation_date::text, value, value_unit
            from macro_observations
            where role='inflation' and value is not null
            order by observation_date desc
            offset 1 limit 1
            """
        )
        hold_inf = cur.fetchone()

    latest: dict[str, dict[str, Any]] = {}
    for role, series_id, d, value, value_unit in latest_rows:
        latest[role] = {"series_id": series_id, "date": d, "value": float(value), "value_unit": value_unit}
    if hold_inf:
        latest["inflation"] = {
            "series_id": hold_inf[1],
            "date": hold_inf[2],
            "value": float(hold_inf[3]),
            "value_unit": hold_inf[4],
        }
    if not latest:
        raise EvaluatorError("no macro_observations for holdout")
    if not _inflation_ok(latest):
        raise EvaluatorError("inflation unit invalid for holdout")

    regime, scored = _score_from_latest(latest)
    fail = len(scored) < DEFAULT_THRESHOLDS["holdout_min_sample"]
    for row in scored:
        overall = float(row["overall"])
        if overall < DEFAULT_THRESHOLDS["score_min"] or overall > DEFAULT_THRESHOLDS["score_max"]:
            fail = True

    dataset = {
        "kind": "holdout_prior_inflation",
        "inflation_date": (latest.get("inflation") or {}).get("date"),
        "regime": regime,
    }
    return _persist(
        conn,
        eval_kind="holdout",
        artifact_type=artifact_type,
        artifact_ref=artifact_ref,
        candidate_version=candidate_version,
        dataset_id="macro-holdout-prior-inflation",
        dataset_hash=_hash(dataset),
        sample_count=len(scored),
        metrics={"industries": [{"industry_id": r["industry_id"], "overall": r["overall"]} for r in scored], "regime": regime},
        baseline=None,
        status="FAIL" if fail else "PASS",
    )


def _persist(
    conn: psycopg.Connection,
    *,
    eval_kind: str,
    artifact_type: str,
    artifact_ref: str,
    candidate_version: str,
    dataset_id: str,
    dataset_hash: str,
    sample_count: int,
    metrics: dict[str, Any],
    baseline: dict[str, Any] | None,
    status: str,
) -> dict[str, Any]:
    evaluation_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()
    row = {
        "evaluation_id": evaluation_id,
        "eval_kind": eval_kind,
        "evaluator_version": EVALUATOR_VERSION,
        "artifact_type": artifact_type,
        "artifact_ref": artifact_ref,
        "candidate_version": candidate_version,
        "dataset_id": dataset_id,
        "dataset_hash": dataset_hash,
        "sample_count": sample_count,
        "metrics": metrics,
        "baseline": baseline,
        "thresholds": DEFAULT_THRESHOLDS,
        "status": status,
        "generated_at": generated_at,
    }
    output_hash = _hash(_canonical_artifact(row))
    row["output_hash"] = output_hash
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into governance_evaluations (
              evaluation_id, eval_kind, evaluator_version, artifact_type, artifact_ref,
              candidate_version, dataset_id, dataset_hash, sample_count, metrics, baseline,
              thresholds, status, output_hash, generated_at
            ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s)
            """,
            (
                evaluation_id,
                eval_kind,
                EVALUATOR_VERSION,
                artifact_type,
                artifact_ref,
                candidate_version,
                dataset_id,
                dataset_hash,
                sample_count,
                json.dumps(metrics),
                json.dumps(baseline) if baseline is not None else None,
                json.dumps(DEFAULT_THRESHOLDS),
                status,
                output_hash,
                generated_at,
            ),
        )
    conn.commit()
    return row


def load_recorded_evaluation(conn: psycopg.Connection, evaluation_id: str) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select evaluation_id::text, eval_kind, evaluator_version, artifact_type, artifact_ref,
                   candidate_version, dataset_id, dataset_hash, sample_count, metrics, baseline,
                   thresholds, status, output_hash, generated_at::text
            from governance_evaluations where evaluation_id=%s::uuid
            """,
            (evaluation_id,),
        )
        row = cur.fetchone()
    if not row:
        raise EvaluatorError(f"evaluation not found: {evaluation_id}")
    artifact = {
        "evaluation_id": row[0],
        "eval_kind": row[1],
        "evaluator_version": row[2],
        "artifact_type": row[3],
        "artifact_ref": row[4],
        "candidate_version": row[5],
        "dataset_id": row[6],
        "dataset_hash": row[7],
        "sample_count": row[8],
        "metrics": row[9] if isinstance(row[9], dict) else json.loads(row[9] or "{}"),
        "baseline": row[10] if row[10] is None or isinstance(row[10], dict) else json.loads(row[10]),
        "thresholds": row[11] if isinstance(row[11], dict) else json.loads(row[11] or "{}"),
        "status": row[12],
        "generated_at": row[14],
        "output_hash": row[13],
    }
    recomputed = _hash(_canonical_artifact(artifact))
    if recomputed != artifact["output_hash"]:
        raise EvaluatorError("evaluation output_hash mismatch")
    return artifact
