from pathlib import Path

from app.agents.final_gate import (
    approved_claim_catalog,
    evaluate_final_selector_gate,
    materialize_final_selector,
)
from app.governance.evaluator import evaluate_candidate
from app.governance.proposals import (
    GovernanceError,
    assert_candidate_hash_current,
    assert_eval_bound_to_proposal,
    assert_replay_holdout_same_candidate,
)

_RESEARCH = {
    "synthesis": "regime is expansion",
    "claims": [{"claim": "regime is expansion", "evidence_id": "regime"}],
    "bear_case": ["policy risk"],
}
_BUNDLE = {
    "ticker": "MSFT",
    "evidence": [{"evidence_id": "regime", "kind": "regime", "payload": {"regime": "expansion"}}],
}
_IDS = {
    "status": "WATCH",
    "rationale_claim_refs": ["claim:0"],
    "bear_case_claim_refs": ["research_bear:0"],
    "risks_claim_refs": ["research_bear:0"],
    "invalidation_claim_refs": ["claim:0"],
    "evidence_refs": ["regime"],
    "claim_refs": ["claim:0", "research_bear:0"],
}


def _gate(output):
    return evaluate_final_selector_gate(
        output,
        allowed_evidence_ids={"regime"},
        evidence_bundle=_BUNDLE,
        research_output=_RESEARCH,
    )


def test_ids_only_final_selector_pass_and_server_reconstructs_text():
    status, reasons = _gate(_IDS)
    assert status == "PASS", reasons
    materialized = materialize_final_selector(_IDS, approved_claim_catalog(_RESEARCH))
    assert materialized["rationale"] == "regime is expansion"
    assert materialized["bear_case"] == ["policy risk"]


def test_negated_approved_claim_fails():
    status, reasons = _gate({**_IDS, "rationale": "regime is not expansion"})
    assert status == "FAIL"
    assert any("not_bound_to_claim_refs" in r for r in reasons)


def test_uncited_catalog_claim_fails():
    status, reasons = _gate({**_IDS, "rationale": "policy risk"})
    assert status == "FAIL"
    assert any("not_bound_to_claim_refs" in r for r in reasons)


def test_short_new_predicate_fails():
    status, reasons = _gate({**_IDS, "rationale": "regime may crash"})
    assert status == "FAIL"
    assert any("not_bound_to_claim_refs" in r for r in reasons)


def test_citing_claim0_while_sentence_is_other_claim_fails():
    status, reasons = _gate(
        {
            **_IDS,
            "rationale_claim_refs": ["claim:0"],
            "rationale": "policy risk",
        }
    )
    assert status == "FAIL"
    assert any("rationale_not_bound_to_claim_refs" in r for r in reasons)


def test_schema_valid_nonexistent_model_fails_evaluation(tmp_path: Path):
    cfg = tmp_path / "config"
    cfg.mkdir()
    roles = "\n".join(
        f"{role}:\n  model: THIS_MODEL_DOES_NOT_EXIST\n  reasoning_effort: medium"
        for role in (
            "market_agent",
            "industry_agent",
            "company_agent",
            "event_agent",
            "research_agent",
            "research_qa_agent",
            "adversarial_agent",
            "final_selector_agent",
        )
    )
    (cfg / "llm_profiles.missing.yaml").write_text(
        f"version: missing-model-v1\nprovider: openai\napi: responses\n{roles}\n",
        encoding="utf-8",
    )
    replay = evaluate_candidate(
        "llm_profile", "llm_profiles.missing.yaml", "missing-model-v1", eval_kind="replay", repo=tmp_path
    )
    holdout = evaluate_candidate(
        "llm_profile", "llm_profiles.missing.yaml", "missing-model-v1", eval_kind="holdout", repo=tmp_path
    )
    assert replay["ok"] is False, replay
    assert holdout["ok"] is False, holdout
    assert "unavailable model" in (replay["metrics"].get("error") or "").lower()


def test_cross_artifact_pass_eval_cannot_bind():
    proposal = {
        "artifact_type": "llm_profile",
        "artifact_ref": "llm_profiles.v0.2.yaml",
        "to_version": "llm-profile-v0.2",
    }
    recorded = {
        "artifact_type": "quant_rule",
        "artifact_ref": "quant_rules.v0.1.yaml",
        "candidate_version": "quant-rules-v0.1",
        "metrics": {"artifact_content_hash": "abc"},
        "status": "PASS",
    }
    try:
        assert_eval_bound_to_proposal(proposal, recorded, label="replay")
        assert False, "expected GovernanceError"
    except GovernanceError as exc:
        assert "artifact_type" in str(exc)


def test_replay_holdout_different_hashes_cannot_pair():
    replay = {
        "artifact_type": "llm_profile",
        "artifact_ref": "llm_profiles.v0.2.yaml",
        "candidate_version": "llm-profile-v0.2",
        "metrics": {"artifact_content_hash": "aaa"},
    }
    holdout = {
        **replay,
        "metrics": {"artifact_content_hash": "bbb"},
    }
    try:
        assert_replay_holdout_same_candidate(replay, holdout)
        assert False, "expected GovernanceError"
    except GovernanceError as exc:
        assert "content hash" in str(exc)


def test_artifact_changed_after_eval_cannot_freeze(tmp_path: Path):
    cfg = tmp_path / "config"
    cfg.mkdir()
    path = cfg / "llm_profiles.v0.2.yaml"
    path.write_text("version: llm-profile-v0.2\nnote: original\n", encoding="utf-8")
    recorded = {
        "artifact_type": "llm_profile",
        "artifact_ref": "llm_profiles.v0.2.yaml",
        "candidate_version": "llm-profile-v0.2",
        "metrics": {"artifact_content_hash": "deadbeef"},
    }
    proposal = {
        "artifact_type": "llm_profile",
        "artifact_ref": "llm_profiles.v0.2.yaml",
        "to_version": "llm-profile-v0.2",
    }
    try:
        assert_candidate_hash_current(proposal, recorded, repo=tmp_path)
        assert False, "expected GovernanceError"
    except GovernanceError as exc:
        assert "changed after evaluation" in str(exc)
    path.write_text("version: llm-profile-v0.2\nnote: mutated\n", encoding="utf-8")
    try:
        assert_candidate_hash_current(proposal, recorded, repo=tmp_path)
        assert False, "expected GovernanceError"
    except GovernanceError as exc:
        assert "changed after evaluation" in str(exc)
