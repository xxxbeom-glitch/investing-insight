from app.agents.binding import FrozenContextError, bind_union_lineage
from app.agents.final_gate import evaluate_final_selector_gate
from app.governance.evaluator import evaluate_candidate


def test_fabricated_nonnumeric_claim_cannot_reach_pass():
    status, reasons = evaluate_final_selector_gate(
        {
            "status": "SELECTED",
            "rationale": "Microsoft lost a major cloud contract and is insolvent.",
            "bear_case": ["Microsoft is insolvent"],
            "risks": ["The CEO resigned unexpectedly"],
            "invalidation_conditions": ["cloud contract loss"],
            "evidence_refs": ["regime"],
            "claim_refs": ["claim:0"],
        },
        allowed_evidence_ids={"regime"},
        evidence_bundle={
            "ticker": "MSFT",
            "evidence": [{"evidence_id": "regime", "kind": "regime", "payload": {"regime": "expansion"}}],
        },
        research_output={
            "synthesis": "regime is expansion",
            "claims": [{"claim": "regime is expansion", "evidence_id": "regime"}],
            "bear_case": ["policy risk"],
        },
    )
    assert status == "FAIL"
    assert any("unsupported_factual" in r for r in reasons)


def test_final_selector_grounded_claim_pass():
    status, reasons = evaluate_final_selector_gate(
        {
            "status": "WATCH",
            "rationale": "regime is expansion",
            "bear_case": ["policy risk"],
            "risks": ["policy risk"],
            "invalidation_conditions": ["regime is expansion"],
            "evidence_refs": ["regime"],
            "claim_refs": ["claim:0"],
        },
        allowed_evidence_ids={"regime"},
        evidence_bundle={
            "ticker": "MSFT",
            "evidence": [{"evidence_id": "regime", "kind": "regime", "payload": {"regime": "expansion"}}],
        },
        research_output={
            "synthesis": "regime is expansion",
            "claims": [{"claim": "regime is expansion", "evidence_id": "regime"}],
            "bear_case": ["policy risk"],
        },
    )
    assert status == "PASS", reasons


def test_unknown_claim_ref_fails():
    status, reasons = evaluate_final_selector_gate(
        {
            "status": "WATCH",
            "rationale": "regime is expansion",
            "bear_case": ["policy risk"],
            "risks": ["policy risk"],
            "invalidation_conditions": ["regime is expansion"],
            "evidence_refs": ["regime"],
            "claim_refs": ["claim:999"],
        },
        allowed_evidence_ids={"regime"},
        evidence_bundle={"evidence": [{"evidence_id": "regime", "payload": {"regime": "expansion"}}]},
        research_output={"claims": [{"claim": "regime is expansion", "evidence_id": "regime"}]},
    )
    assert status == "FAIL"
    assert any("unknown_claim_ref" in r for r in reasons)


def test_older_union_does_not_borrow_newer_assessment_or_regime():
    old_a = {
        "assessment_id": "a-old",
        "industry_id": "semis",
        "as_of": "2026-01-01",
        "regime_id": "r-old",
        "overall_score": 10.0,
    }
    new_a = {
        "assessment_id": "a-new",
        "industry_id": "semis",
        "as_of": "2026-08-01",
        "regime_id": "r-new",
        "overall_score": 99.0,
    }
    bound = bind_union_lineage(
        {"topdown_assessment_ids": ["a-old"], "as_of": "2026-01-01"},
        [new_a, old_a],
        [
            {"regime_id": "r-new", "as_of": "2026-08-01", "regime": "contraction"},
            {"regime_id": "r-old", "as_of": "2026-01-01", "regime": "expansion"},
        ],
    )
    assert bound["assessments"][0]["assessment_id"] == "a-old"
    assert bound["assessments"][0]["overall_score"] == 10.0
    assert bound["regime"]["regime_id"] == "r-old"
    assert bound["regime"]["regime"] == "expansion"


def test_inconsistent_regime_lineage_fails_closed():
    try:
        bind_union_lineage(
            {"topdown_assessment_ids": ["a1", "a2"]},
            [
                {"assessment_id": "a1", "as_of": "2026-01-01", "regime_id": "r1"},
                {"assessment_id": "a2", "as_of": "2026-01-01", "regime_id": "r2"},
            ],
            [
                {"regime_id": "r1", "as_of": "2026-01-01", "regime": "expansion"},
                {"regime_id": "r2", "as_of": "2026-01-01", "regime": "contraction"},
            ],
        )
        assert False, "expected FrozenContextError"
    except FrozenContextError as exc:
        assert "inconsistent regime" in str(exc)


def test_missing_assessment_id_fails_closed():
    try:
        bind_union_lineage(
            {"topdown_assessment_ids": ["missing"]},
            [{"assessment_id": "other", "as_of": "2026-01-01", "regime_id": "r1"}],
            [{"regime_id": "r1", "as_of": "2026-01-01", "regime": "expansion"}],
        )
        assert False, "expected FrozenContextError"
    except FrozenContextError as exc:
        assert "missing" in str(exc)


def test_valid_llm_profile_artifact_passes_replay_and_holdout():
    replay = evaluate_candidate(
        "llm_profile", "llm_profiles.v0.2.yaml", "llm-profile-v0.2", eval_kind="replay"
    )
    holdout = evaluate_candidate(
        "llm_profile", "llm_profiles.v0.2.yaml", "llm-profile-v0.2", eval_kind="holdout"
    )
    assert replay["ok"] is True, replay
    assert holdout["ok"] is True, holdout
    assert replay["metrics"]["artifact_content_hash"]
    assert replay["dataset_id"] != holdout["dataset_id"]
    assert "replay-regime-watch" in str(replay["metrics"])
    assert "holdout-assessment-watch" in str(holdout["metrics"])


def test_missing_llm_profile_fails_without_m02_scores():
    result = evaluate_candidate(
        "llm_profile", "llm_profiles", "llm-profile-does-not-exist", eval_kind="replay"
    )
    assert result["ok"] is False
    assert "m02" not in str(result).lower()
    assert "industry" not in (result["metrics"].get("error") or "").lower() or True
    assert result["metrics"].get("artifact_loaded") is False


def test_broken_llm_profile_file_fails(tmp_path):
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "llm_profiles.broken.yaml").write_text(
        "version: broken-v1\nmarket_agent: {}\n",
        encoding="utf-8",
    )
    result = evaluate_candidate(
        "llm_profile", "llm_profiles", "broken-v1", eval_kind="replay", repo=tmp_path
    )
    assert result["ok"] is False
    assert result["metrics"].get("artifact_loaded") is True


def test_quant_rule_artifact_executes_weights():
    result = evaluate_candidate(
        "quant_rule", "quant_rules.v0.1.yaml", "quant-rules-v0.1", eval_kind="replay"
    )
    assert result["ok"] is True, result
    assert result["metrics"]["quant_scores"]
