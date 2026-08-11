"""Artifact-aware replay/holdout evaluator (ER3-P1-03)."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg
import yaml

from app.agents.final_gate import evaluate_final_selector_gate
from app.agents.profiles import MULTIAGENT_ROLES, MultiAgentProfiles
from app.agents.runner import evaluate_adversarial_gate, evaluate_research_qa_gate
from app.llm_profiles import LlmProfiles

REPO_ROOT = Path(__file__).resolve().parents[4]
EVALUATOR_VERSION = "governance-eval-v0.2"
DEFAULT_THRESHOLDS = {
    "replay_gate_pass_rate_min": 1.0,
    "holdout_gate_pass_rate_min": 1.0,
    "holdout_min_sample": 1,
    "quant_weight_sum": 100,
    "quant_score_min": 0.0,
    "quant_score_max": 100.0,
}


class EvaluatorError(RuntimeError):
    pass


def _hash(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _canonical_artifact(row: dict[str, Any]) -> dict[str, Any]:
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


# Frozen packets used as replay vs holdout datasets (disjoint).
_REPLAY_PACKETS: list[dict[str, Any]] = [
    {
        "packet_id": "replay-regime-watch",
        "allowed_evidence_ids": ["regime"],
        "evidence_bundle": {
            "ticker": "MSFT",
            "allowed_evidence_ids": ["regime"],
            "evidence": [{"evidence_id": "regime", "kind": "regime", "payload": {"regime": "expansion"}}],
        },
        "research": {
            "synthesis": "regime is expansion",
            "claims": [{"claim": "regime is expansion", "evidence_id": "regime"}],
            "bear_case": ["policy risk"],
            "evidence_refs": ["regime"],
            "unsupported_or_missing": [],
        },
        "adversarial": {
            "status": "PASS",
            "counter_thesis": "policy risk",
            "broken_assumptions": [],
            "gate_blockers": [],
        },
        "qa": {"status": "PASS", "failed_claims": [], "warnings": []},
        "final": {
            "status": "WATCH",
            "rationale": "regime is expansion",
            "bear_case": ["policy risk"],
            "risks": ["policy risk"],
            "invalidation_conditions": ["regime is expansion"],
            "evidence_refs": ["regime"],
            "claim_refs": ["claim:0"],
        },
    }
]

_HOLDOUT_PACKETS: list[dict[str, Any]] = [
    {
        "packet_id": "holdout-assessment-watch",
        "allowed_evidence_ids": ["assessment:software"],
        "evidence_bundle": {
            "ticker": "MSFT",
            "allowed_evidence_ids": ["assessment:software"],
            "evidence": [
                {
                    "evidence_id": "assessment:software",
                    "kind": "industry_assessment",
                    "payload": {"industry_id": "software", "overall_score": 61.7},
                }
            ],
        },
        "research": {
            "synthesis": "software assessment is constructive",
            "claims": [{"claim": "software assessment is constructive", "evidence_id": "assessment:software"}],
            "bear_case": ["multiple compression"],
            "evidence_refs": ["assessment:software"],
            "unsupported_or_missing": [],
        },
        "adversarial": {
            "status": "PASS",
            "counter_thesis": "multiple compression",
            "broken_assumptions": [],
            "gate_blockers": [],
        },
        "qa": {"status": "PASS", "failed_claims": [], "warnings": []},
        "final": {
            "status": "WATCH",
            "rationale": "software assessment is constructive",
            "bear_case": ["multiple compression"],
            "risks": ["multiple compression"],
            "invalidation_conditions": ["software assessment is constructive"],
            "evidence_refs": ["assessment:software"],
            "claim_refs": ["claim:0"],
        },
    }
]

_QUANT_REPLAY_VECTORS = [
    {"growth": 60.0, "quality": 55.0, "cashflow": 50.0, "health": 52.0, "valuation": 40.0, "momentum": 45.0},
]
_QUANT_HOLDOUT_VECTORS = [
    {"growth": 30.0, "quality": 70.0, "cashflow": 65.0, "health": 48.0, "valuation": 80.0, "momentum": 20.0},
]


def resolve_candidate_artifact(
    artifact_type: str,
    artifact_ref: str,
    candidate_version: str,
    *,
    repo: Path | None = None,
) -> dict[str, Any]:
    """Load the actual candidate file and hash its bytes. Missing/invalid → error."""
    root = repo or REPO_ROOT
    path = _locate_artifact(root, artifact_type, artifact_ref, candidate_version)
    text = path.read_text(encoding="utf-8")
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    parsed: Any = None
    if path.suffix in {".yaml", ".yml", ".json"}:
        parsed = yaml.safe_load(text) if path.suffix != ".json" else json.loads(text)
        if isinstance(parsed, dict) and parsed.get("version") and str(parsed.get("version")) != str(candidate_version):
            raise EvaluatorError(
                f"artifact version mismatch: file={parsed.get('version')} candidate={candidate_version}"
            )
    return {
        "path": str(path.relative_to(root)).replace("\\", "/"),
        "text": text,
        "parsed": parsed,
        "content_hash": content_hash,
        "artifact_type": artifact_type,
        "artifact_ref": artifact_ref,
        "candidate_version": candidate_version,
    }


def _locate_artifact(root: Path, artifact_type: str, artifact_ref: str, candidate_version: str) -> Path:
    config = root / "config"
    if artifact_type in {"llm_profile", "model"}:
        for p in sorted(config.glob("llm_profiles*.yaml")):
            raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            if str(raw.get("version")) == str(candidate_version) or p.name == artifact_ref or p.stem == artifact_ref:
                return p
        raise EvaluatorError(f"llm_profile artifact not found for version={candidate_version!r}")
    if artifact_type == "prompt":
        direct = config / "prompts" / artifact_ref
        if direct.is_file():
            return direct
        nested = config / "prompts" / "agents" / artifact_ref
        if nested.is_file():
            return nested
        raise EvaluatorError(f"prompt artifact not found: {artifact_ref}")
    if artifact_type == "quant_rule":
        for p in sorted(config.glob("quant_rules*.yaml")):
            raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            if str(raw.get("version")) == str(candidate_version) or p.name == artifact_ref:
                return p
        raise EvaluatorError(f"quant_rule artifact not found for version={candidate_version!r}")
    if artifact_type == "score_rule":
        for p in sorted(config.glob("industry_rules*.yaml")):
            raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            if str(raw.get("version")) == str(candidate_version) or p.name == artifact_ref:
                return p
        raise EvaluatorError(f"score_rule artifact not found for version={candidate_version!r}")
    raise EvaluatorError(f"unsupported artifact_type: {artifact_type}")


def _validate_llm_profile(parsed: Any) -> dict[str, Any]:
    if not isinstance(parsed, dict):
        raise EvaluatorError("llm_profile must be a mapping")
    try:
        profiles = MultiAgentProfiles.model_validate(parsed)
        return {"kind": "multiagent", "version": profiles.version, "roles": list(MULTIAGENT_ROLES)}
    except Exception:
        try:
            profiles = LlmProfiles.model_validate(parsed)
            return {
                "kind": "research",
                "version": profiles.version,
                "roles": ["company_research", "research_qa", "final_judgment"],
            }
        except Exception as exc:  # noqa: BLE001
            raise EvaluatorError(f"llm_profile invalid: {exc}") from exc


def _score_quant(rule: dict[str, Any], vector: dict[str, float]) -> float:
    weights = rule.get("weights") or {}
    if not isinstance(weights, dict) or not weights:
        raise EvaluatorError("quant_rule missing weights")
    total_w = sum(float(v) for v in weights.values())
    if abs(total_w - float(DEFAULT_THRESHOLDS["quant_weight_sum"])) > 1e-6:
        raise EvaluatorError(f"quant_rule weights must sum to 100, got {total_w}")
    acc = 0.0
    for key, w in weights.items():
        acc += float(vector.get(key, 0.0)) * float(w) / 100.0
    return acc


def _replay_gates(packets: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    pass_n = 0
    for pkt in packets:
        qa_st, qa_r = evaluate_research_qa_gate(
            pkt["qa"],
            research_output=pkt["research"],
            allowed_evidence_ids=pkt["allowed_evidence_ids"],
        )
        adv_st, adv_r = evaluate_adversarial_gate(pkt["adversarial"])
        final_st, final_r = evaluate_final_selector_gate(
            pkt["final"],
            allowed_evidence_ids=pkt["allowed_evidence_ids"],
            evidence_bundle=pkt["evidence_bundle"],
            research_output=pkt["research"],
            adversarial_output=pkt["adversarial"],
        )
        ok = qa_st == "PASS" and adv_st == "PASS" and final_st == "PASS"
        if ok:
            pass_n += 1
        results.append(
            {
                "packet_id": pkt["packet_id"],
                "qa": qa_st,
                "adversarial": adv_st,
                "final": final_st,
                "reasons": qa_r + adv_r + final_r,
            }
        )
    n = len(packets) or 1
    return {"results": results, "gate_pass_rate": pass_n / n, "sample_count": len(packets)}


def evaluate_candidate(
    artifact_type: str,
    artifact_ref: str,
    candidate_version: str,
    *,
    eval_kind: str,
    repo: Path | None = None,
) -> dict[str, Any]:
    """Run the candidate artifact itself. Does not use unrelated M02 industry scores."""
    try:
        loaded = resolve_candidate_artifact(artifact_type, artifact_ref, candidate_version, repo=repo)
    except EvaluatorError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "artifact_content_hash": None,
            "sample_count": 0,
            "metrics": {"error": str(exc), "artifact_loaded": False},
            "baseline": None,
            "dataset_id": f"{eval_kind}-{artifact_type}-missing",
            "dataset_hash": _hash({"kind": eval_kind, "error": str(exc)}),
        }

    metrics: dict[str, Any] = {
        "artifact_loaded": True,
        "artifact_path": loaded["path"],
        "artifact_content_hash": loaded["content_hash"],
        "artifact_type": artifact_type,
        "candidate_version": candidate_version,
    }
    baseline: dict[str, Any] | None = {"artifact_content_hash": loaded["content_hash"]}
    fail = False
    sample_count = 0
    dataset: dict[str, Any] = {"kind": eval_kind, "artifact_type": artifact_type, "path": loaded["path"]}

    if artifact_type in {"llm_profile", "model"}:
        try:
            meta = _validate_llm_profile(loaded["parsed"])
            metrics["profile"] = meta
        except EvaluatorError as exc:
            fail = True
            metrics["error"] = str(exc)
            meta = None
        packets = _REPLAY_PACKETS if eval_kind == "replay" else _HOLDOUT_PACKETS
        dataset["packet_ids"] = [p["packet_id"] for p in packets]
        gated = _replay_gates(packets)
        metrics["gates"] = gated
        sample_count = gated["sample_count"]
        min_rate = DEFAULT_THRESHOLDS["replay_gate_pass_rate_min"] if eval_kind == "replay" else DEFAULT_THRESHOLDS["holdout_gate_pass_rate_min"]
        if gated["gate_pass_rate"] < min_rate:
            fail = True
        if sample_count < DEFAULT_THRESHOLDS["holdout_min_sample"]:
            fail = True
        if meta is None:
            fail = True
    elif artifact_type == "quant_rule":
        vectors = _QUANT_REPLAY_VECTORS if eval_kind == "replay" else _QUANT_HOLDOUT_VECTORS
        scores = []
        try:
            for vec in vectors:
                sc = _score_quant(loaded["parsed"] or {}, vec)
                if sc < DEFAULT_THRESHOLDS["quant_score_min"] or sc > DEFAULT_THRESHOLDS["quant_score_max"]:
                    fail = True
                scores.append(sc)
        except EvaluatorError as exc:
            fail = True
            metrics["error"] = str(exc)
        metrics["quant_scores"] = scores
        sample_count = len(vectors)
        dataset["vector_count"] = sample_count
        baseline = {"weights": (loaded["parsed"] or {}).get("weights")}
    elif artifact_type == "prompt":
        text = loaded["text"]
        if len(text.strip()) < 20:
            fail = True
            metrics["error"] = "prompt too short"
        packets = _REPLAY_PACKETS if eval_kind == "replay" else _HOLDOUT_PACKETS
        gated = _replay_gates(packets)
        metrics["gates"] = gated
        sample_count = gated["sample_count"]
        if gated["gate_pass_rate"] < 1.0:
            fail = True
    elif artifact_type == "score_rule":
        parsed = loaded["parsed"] or {}
        if not parsed.get("industries"):
            fail = True
            metrics["error"] = "score_rule missing industries"
        sample_count = len(parsed.get("industries") or [])
        metrics["industry_count"] = sample_count
        if sample_count < 1:
            fail = True
    else:
        raise EvaluatorError(f"unsupported artifact_type: {artifact_type}")

    return {
        "ok": not fail,
        "artifact_content_hash": loaded["content_hash"],
        "sample_count": sample_count,
        "metrics": metrics,
        "baseline": baseline,
        "dataset_id": f"{eval_kind}-{artifact_type}-{loaded['content_hash'][:12]}",
        "dataset_hash": _hash(dataset),
    }


def run_replay_evaluation(
    conn: psycopg.Connection,
    *,
    artifact_type: str,
    artifact_ref: str,
    candidate_version: str,
    repo: Path | None = None,
) -> dict[str, Any]:
    result = evaluate_candidate(
        artifact_type, artifact_ref, candidate_version, eval_kind="replay", repo=repo
    )
    return _persist(
        conn,
        eval_kind="replay",
        artifact_type=artifact_type,
        artifact_ref=artifact_ref,
        candidate_version=candidate_version,
        dataset_id=result["dataset_id"],
        dataset_hash=result["dataset_hash"],
        sample_count=result["sample_count"],
        metrics=result["metrics"],
        baseline=result["baseline"],
        status="PASS" if result["ok"] else "FAIL",
    )


def run_holdout_evaluation(
    conn: psycopg.Connection,
    *,
    artifact_type: str,
    artifact_ref: str,
    candidate_version: str,
    repo: Path | None = None,
) -> dict[str, Any]:
    result = evaluate_candidate(
        artifact_type, artifact_ref, candidate_version, eval_kind="holdout", repo=repo
    )
    return _persist(
        conn,
        eval_kind="holdout",
        artifact_type=artifact_type,
        artifact_ref=artifact_ref,
        candidate_version=candidate_version,
        dataset_id=result["dataset_id"],
        dataset_hash=result["dataset_hash"],
        sample_count=result["sample_count"],
        metrics=result["metrics"],
        baseline=result["baseline"],
        status="PASS" if result["ok"] else "FAIL",
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
