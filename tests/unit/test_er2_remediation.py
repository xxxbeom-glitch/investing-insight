from app.agents.binding import context_hash
from app.agents.evidence import pick_quant_record
from app.agents.final_gate import evaluate_final_selector_gate
from app.governance.proposals import GovernanceError, _require_recorded_eval


def test_context_hash_stable_for_same_frozen():
    frozen = {"union": {"union_id": "u1"}, "regime": {"regime": "expansion"}, "quant_records": []}
    assert context_hash(frozen) == context_hash(frozen)
    other = {**frozen, "regime": {"regime": "contraction"}}
    assert context_hash(frozen) != context_hash(other)


def test_quant_picks_frozen_run_not_uuid_order():
    security_id = "sec-a"
    frozen_run = "00000000-0000-0000-0000-000000000001"
    other_run = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    records = [
        {"run_id": other_run, "security_id": security_id, "total_score": 99.0},
        {"run_id": frozen_run, "security_id": security_id, "total_score": 11.0},
    ]
    hit = pick_quant_record(records, security_id=security_id, frozen_run_id=frozen_run)
    assert hit is not None
    assert hit["total_score"] == 11.0
    assert pick_quant_record(records, security_id=security_id, frozen_run_id=None) is None
    assert pick_quant_record(records, security_id="other", frozen_run_id=frozen_run) is None


def test_final_selector_unknown_ref_fails():
    status, reasons = evaluate_final_selector_gate(
        {
            "status": "WATCH",
            "rationale": "ok",
            "bear_case": ["b"],
            "risks": ["r"],
            "invalidation_conditions": ["i"],
            "evidence_refs": ["not-allowed"],
        },
        allowed_evidence_ids={"regime"},
        evidence_bundle={"evidence": [{"evidence_id": "regime"}]},
    )
    assert status == "FAIL"
    assert any("unknown_ref" in r for r in reasons)


def test_final_selector_selected_requires_risk_arrays():
    status, reasons = evaluate_final_selector_gate(
        {
            "status": "SELECTED",
            "rationale": "buy",
            "bear_case": [],
            "risks": [],
            "invalidation_conditions": [],
            "evidence_refs": [],
        },
        allowed_evidence_ids={"regime"},
        evidence_bundle={"evidence": [{"evidence_id": "regime"}]},
    )
    assert status == "FAIL"
    assert any("selected_empty_bear_case" in r for r in reasons)
    assert any("selected_empty_risks" in r for r in reasons)
    assert any("selected_empty_invalidation_conditions" in r for r in reasons)
    assert any("selected_empty_evidence_refs" in r for r in reasons)


def test_final_selector_new_unsupported_number_fails():
    status, reasons = evaluate_final_selector_gate(
        {
            "status": "WATCH",
            "rationale_claim_refs": ["claim:0"],
            "bear_case_claim_refs": ["research_bear:0"],
            "risks_claim_refs": ["research_bear:0"],
            "invalidation_claim_refs": ["claim:0"],
            "evidence_refs": ["regime"],
        },
        allowed_evidence_ids={"regime"},
        evidence_bundle={"evidence": [{"evidence_id": "regime", "value": 2.5}]},
        research_output={
            "claims": [{"claim": "revenue is 999999.0 with no packet support", "evidence_id": "regime"}],
            "bear_case": ["b"],
        },
    )
    assert status == "FAIL"
    assert any("unsupported_numeric" in r for r in reasons)


def test_hand_authored_pass_json_rejected_without_evaluation_id():
    class _Conn:
        pass

    try:
        _require_recorded_eval(_Conn(), "replay", "replay", None, {"status": "PASS", "dataset_id": "x", "metrics": {}})
        assert False, "expected GovernanceError"
    except GovernanceError as exc:
        assert "evaluation_id" in str(exc)
