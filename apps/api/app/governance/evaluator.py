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

from pydantic import ValidationError

from app.agents.final_gate import approved_claim_catalog, evaluate_final_selector_gate
from app.agents.mock_client import MockStructuredClient
from app.agents.profiles import MULTIAGENT_ROLES, MultiAgentProfiles
from app.agents.runner import (
    ROLE_SCHEMA,
    _system_prompt,
    build_role_packet,
    evaluate_adversarial_gate,
    evaluate_research_qa_gate,
)
from app.research.openai_responses import ModelUnavailableError
from app.research.schema_validate import load_schema, validate_against_schema

REPO_ROOT = Path(__file__).resolve().parents[4]
EVALUATOR_VERSION = "governance-eval-v0.4"
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
            "rationale_claim_refs": ["claim:0"],
            "bear_case_claim_refs": ["research_bear:0"],
            "risks_claim_refs": ["research_bear:0"],
            "invalidation_claim_refs": ["claim:0"],
            "evidence_refs": ["regime"],
            "claim_refs": ["claim:0", "research_bear:0"],
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
            "rationale_claim_refs": ["claim:0"],
            "bear_case_claim_refs": ["research_bear:0"],
            "risks_claim_refs": ["research_bear:0"],
            "invalidation_claim_refs": ["claim:0"],
            "evidence_refs": ["assessment:software"],
            "claim_refs": ["claim:0", "research_bear:0"],
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
    """Load the actual candidate file and hash canonical UTF-8 text (newline-normalized)."""
    root = repo or REPO_ROOT
    path = _locate_artifact(root, artifact_type, artifact_ref, candidate_version)
    # Canonical UTF-8 text hash after Path.read_text (newline-normalized).
    # Archive bytes on CRLF checkouts may differ; attach/approve/freeze use this same method.
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
        "artifact_hash_encoding": "utf8_text_newline_normalized",
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


def _load_baseline_multiagent(repo: Path | None = None) -> MultiAgentProfiles | None:
    for root in (repo or REPO_ROOT, REPO_ROOT):
        for name in ("llm_profiles.v0.2.yaml", "llm_profiles.yaml"):
            path = Path(root) / "config" / name
            if not path.is_file():
                continue
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            try:
                return MultiAgentProfiles.model_validate(raw)
            except (ValidationError, ValueError):
                continue
    return None


def _prompt_target_role(artifact_ref: str) -> str:
    ref = str(artifact_ref or "").replace("\\", "/").lower()
    for role in MULTIAGENT_ROLES:
        if role in ref:
            return role
    return "final_selector_agent"


def _record_baseline_comparison(
    metrics: dict[str, Any],
    baseline: dict[str, Any] | None,
    *,
    candidate_profiles: MultiAgentProfiles | None,
    packets: list[dict[str, Any]],
    repo: Path | None,
) -> dict[str, Any] | None:
    base_profiles = _load_baseline_multiagent(repo)
    if base_profiles is None:
        return baseline
    client = MockStructuredClient()
    try:
        gated = _execute_llm_packets(base_profiles, packets, client)
    except (EvaluatorError, ModelUnavailableError, ValidationError, ValueError) as exc:
        metrics["baseline_error"] = str(exc)
        return baseline
    cand_rate = (metrics.get("gates") or {}).get("gate_pass_rate")
    metrics["baseline_comparison"] = {
        "baseline_version": base_profiles.version,
        "baseline_final_model": base_profiles.final_selector_agent.model,
        "candidate_final_model": (
            candidate_profiles.final_selector_agent.model if candidate_profiles is not None else None
        ),
        "baseline_gate_pass_rate": gated["gate_pass_rate"],
        "candidate_gate_pass_rate": cand_rate,
        "gate_pass_rate_delta": None if cand_rate is None else cand_rate - gated["gate_pass_rate"],
    }
    out = dict(baseline or {})
    out["gate_pass_rate"] = gated["gate_pass_rate"]
    out["final_model"] = base_profiles.final_selector_agent.model
    return out


def execute_role_under_profile(
    agent_role: str,
    packet: dict[str, Any],
    profiles: MultiAgentProfiles,
    client: Any,
    *,
    system_prompt: str | None = None,
) -> dict[str, Any]:
    """Run the real role execution path with the candidate profile's model/effort."""
    role_prof = getattr(profiles, agent_role)
    schema_file, _schema_version = ROLE_SCHEMA[agent_role]
    schema = load_schema(schema_file)
    result = client.create_structured(
        model=role_prof.model,
        reasoning_effort=role_prof.reasoning_effort,
        system_prompt=system_prompt if system_prompt is not None else _system_prompt(agent_role),
        user_payload={**packet, "agent_role": agent_role},
        output_schema=schema,
        schema_name=agent_role,
    )
    if result.resolved_model != role_prof.model:
        raise ModelUnavailableError(
            f"resolved model {result.resolved_model!r} != requested {role_prof.model!r}"
        )
    output = json.loads(result.output_text)
    validate_against_schema(output, schema)
    return output


def _eval_frozen_context(pkt: dict[str, Any]) -> dict[str, Any]:
    if pkt.get("frozen_context"):
        return pkt["frozen_context"]
    bundle = pkt.get("evidence_bundle") or {}
    regime: dict[str, Any] = {"regime": "expansion"}
    assessments: list[dict[str, Any]] = []
    for ev in bundle.get("evidence") or []:
        if not isinstance(ev, dict):
            continue
        eid = str(ev.get("evidence_id") or "")
        payload = ev.get("payload") if isinstance(ev.get("payload"), dict) else {}
        if eid == "regime":
            regime = payload or regime
            if "regime" not in regime:
                regime = {"regime": "expansion", **regime}
        if eid.startswith("assessment"):
            assessments.append(payload)
    ticker = pkt.get("ticker") or bundle.get("ticker") or "TEST"
    return {
        "regime": regime,
        "assessments": assessments,
        "union": {"members": [{"ticker": ticker, "security_id": pkt.get("security_id") or "eval-sec"}]},
    }


def _execute_llm_packets(
    profiles: MultiAgentProfiles,
    packets: list[dict[str, Any]],
    client: Any,
    *,
    system_prompt: str | None = None,
    qa_system_prompt: str | None = None,
) -> dict[str, Any]:
    results = []
    pass_n = 0
    executed_roles: list[str] = []
    for pkt in packets:
        prior: dict[str, Any] = {}
        bundle = dict(pkt.get("evidence_bundle") or {})
        bundle["allowed_evidence_ids"] = pkt["allowed_evidence_ids"]
        frozen = _eval_frozen_context(pkt)
        ticker = pkt.get("ticker") or bundle.get("ticker") or "TEST"
        security_id = pkt.get("security_id") or "eval-sec"
        for role in MULTIAGENT_ROLES:
            packet = build_role_packet(
                agent_role=role,
                run_id="eval",
                snapshot_id="eval",
                frozen_context=frozen,
                security_id=security_id,
                ticker=ticker,
                prior_outputs=prior,
                evidence_bundle=bundle,
            )
            prompt_override = None
            if role == "final_selector_agent" and system_prompt is not None:
                prompt_override = system_prompt
            elif role == "research_qa_agent" and qa_system_prompt is not None:
                prompt_override = qa_system_prompt
            out = execute_role_under_profile(
                role,
                packet,
                profiles,
                client,
                system_prompt=prompt_override,
            )
            prior[role] = out
            if role not in executed_roles:
                executed_roles.append(role)
        research_out = prior["research_agent"]
        qa_out = prior["research_qa_agent"]
        adv_out = prior["adversarial_agent"]
        final_out = prior["final_selector_agent"]
        qa_st, qa_r = evaluate_research_qa_gate(
            qa_out,
            research_output=research_out,
            allowed_evidence_ids=pkt["allowed_evidence_ids"],
        )
        adv_st, adv_r = evaluate_adversarial_gate(adv_out)
        final_st, final_r = evaluate_final_selector_gate(
            final_out,
            allowed_evidence_ids=pkt["allowed_evidence_ids"],
            evidence_bundle=pkt["evidence_bundle"],
            research_output=research_out,
            adversarial_output=adv_out,
        )
        ok = qa_st == "PASS" and adv_st == "PASS" and final_st == "PASS"
        if ok:
            pass_n += 1
        fingerprints = getattr(client, "fingerprints", [])
        results.append(
            {
                "packet_id": pkt["packet_id"],
                "qa": qa_st,
                "adversarial": adv_st,
                "final": final_st,
                "requested_model": profiles.final_selector_agent.model,
                "resolved_model": profiles.final_selector_agent.model,
                "reasoning_effort": profiles.final_selector_agent.reasoning_effort,
                "executed_roles": list(MULTIAGENT_ROLES),
                "behavior_digest": fingerprints[-len(MULTIAGENT_ROLES) :] if fingerprints else [],
                "reasons": qa_r + adv_r + final_r,
            }
        )
    n = len(packets) or 1
    return {
        "results": results,
        "gate_pass_rate": pass_n / n,
        "sample_count": len(packets),
        "executed_roles": executed_roles,
        "executed_role_count": len(executed_roles),
    }


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
        "artifact_hash_encoding": "utf8_text_newline_normalized",
        "artifact_type": artifact_type,
        "candidate_version": candidate_version,
    }
    baseline: dict[str, Any] | None = {"artifact_content_hash": loaded["content_hash"]}
    fail = False
    sample_count = 0
    dataset: dict[str, Any] = {"kind": eval_kind, "artifact_type": artifact_type, "path": loaded["path"]}

    if artifact_type in {"llm_profile", "model"}:
        packets = _REPLAY_PACKETS if eval_kind == "replay" else _HOLDOUT_PACKETS
        dataset["packet_ids"] = [p["packet_id"] for p in packets]
        candidate_profiles: MultiAgentProfiles | None = None
        gated = {"results": [], "gate_pass_rate": 0.0, "sample_count": 0}
        try:
            candidate_profiles = MultiAgentProfiles.model_validate(loaded["parsed"])
            metrics["profile"] = {
                "kind": "multiagent",
                "version": candidate_profiles.version,
                "roles": list(MULTIAGENT_ROLES),
            }
            metrics["requested_models"] = {
                role: getattr(candidate_profiles, role).model for role in MULTIAGENT_ROLES
            }
            metrics["requested_efforts"] = {
                role: getattr(candidate_profiles, role).reasoning_effort for role in MULTIAGENT_ROLES
            }
            client = MockStructuredClient()
            gated = _execute_llm_packets(candidate_profiles, packets, client)
            metrics["executed"] = True
            metrics["executed_roles"] = gated.get("executed_roles")
            metrics["executed_role_count"] = gated.get("executed_role_count")
        except (EvaluatorError, ModelUnavailableError, ValidationError, ValueError, json.JSONDecodeError) as exc:
            fail = True
            metrics["error"] = str(exc)
            metrics["executed"] = False
        metrics["gates"] = gated
        sample_count = gated["sample_count"]
        min_rate = (
            DEFAULT_THRESHOLDS["replay_gate_pass_rate_min"]
            if eval_kind == "replay"
            else DEFAULT_THRESHOLDS["holdout_gate_pass_rate_min"]
        )
        if gated["gate_pass_rate"] < min_rate:
            fail = True
        if sample_count < DEFAULT_THRESHOLDS["holdout_min_sample"]:
            fail = True
        baseline = _record_baseline_comparison(
            metrics,
            baseline,
            candidate_profiles=candidate_profiles,
            packets=packets,
            repo=repo,
        )
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
        packets = _REPLAY_PACKETS if eval_kind == "replay" else _HOLDOUT_PACKETS
        dataset["packet_ids"] = [p["packet_id"] for p in packets]
        gated = {"results": [], "gate_pass_rate": 0.0, "sample_count": 0}
        if len(text.strip()) < 20:
            fail = True
            metrics["error"] = "prompt too short"
            metrics["executed"] = False
        else:
            try:
                profiles = _load_baseline_multiagent(repo)
                if profiles is None:
                    raise EvaluatorError("no multiagent profile available to execute prompt")
                client = MockStructuredClient()
                role = _prompt_target_role(artifact_ref)
                metrics["executed_role"] = role
                gated = _execute_llm_packets(
                    profiles,
                    packets,
                    client,
                    system_prompt=text if role == "final_selector_agent" else None,
                    qa_system_prompt=text if role == "research_qa_agent" else None,
                )
                metrics["executed"] = True
                metrics["executed_roles"] = gated.get("executed_roles")
                metrics["executed_role_count"] = gated.get("executed_role_count")
                metrics["prompt_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            except (EvaluatorError, ModelUnavailableError, ValidationError, ValueError, json.JSONDecodeError) as exc:
                fail = True
                metrics["error"] = str(exc)
                metrics["executed"] = False
        metrics["gates"] = gated
        sample_count = gated["sample_count"]
        if gated["gate_pass_rate"] < 1.0:
            fail = True
        baseline = _record_baseline_comparison(
            metrics,
            baseline,
            candidate_profiles=_load_baseline_multiagent(repo),
            packets=packets,
            repo=repo,
        )
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
