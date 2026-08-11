from app.agents.claim_support import claim_is_supported, claim_unsupported_tokens
from app.agents.final_gate import (
    approved_claim_catalog,
    evaluate_final_selector_gate,
    materialize_final_selector,
)
from app.agents.runner import evaluate_research_qa_gate

_BUNDLE = {
    "ticker": "MSFT",
    "evidence": [{"evidence_id": "regime", "kind": "regime", "payload": {"regime": "expansion"}}],
}


def _ids(*refs: str) -> dict:
    primary = refs[0] if refs else "claim:0"
    return {
        "status": "WATCH",
        "rationale_claim_refs": [primary],
        "bear_case_claim_refs": [primary],
        "risks_claim_refs": [primary],
        "invalidation_claim_refs": [primary],
        "evidence_refs": ["regime"],
        "claim_refs": [primary],
    }


def test_payload_restatement_is_supported():
    evidence = _BUNDLE["evidence"]
    assert claim_is_supported("regime is expansion", "regime", evidence)
    assert claim_unsupported_tokens("regime is expansion", "regime", evidence) == set()


def test_appended_fact_revenue_surged_is_unsupported():
    evidence = _BUNDLE["evidence"]
    text = "regime is expansion and revenue surged"
    assert not claim_is_supported(text, "regime", evidence)
    missing = claim_unsupported_tokens(text, "regime", evidence)
    assert "revenue" in missing
    assert "surged" in missing


def test_appended_fact_not_on_any_denylist_is_unsupported():
    evidence = _BUNDLE["evidence"]
    text = "regime is expansion and capacity booked out"
    assert not claim_is_supported(text, "regime", evidence)
    missing = claim_unsupported_tokens(text, "regime", evidence)
    assert "capacity" in missing
    assert "booked" in missing


def test_negation_of_payload_is_unsupported():
    evidence = _BUNDLE["evidence"]
    assert not claim_is_supported("regime is not expansion", "regime", evidence)
    assert "not" in claim_unsupported_tokens("regime is not expansion", "regime", evidence)


def test_appended_revenue_claim_cannot_reach_judgment_even_if_qa_lies():
    research = {
        "claims": [{"claim": "regime is expansion and revenue surged", "evidence_id": "regime"}],
        "evidence_refs": ["regime"],
    }
    qa_lie = {
        "status": "PASS",
        "failed_claims": [],
        "warnings": [],
        "claim_verdicts": [{"claim_id": "claim:0", "evidence_id": "regime", "support": "SUPPORTED"}],
    }
    qa_st, qa_reasons = evaluate_research_qa_gate(
        qa_lie,
        research_output=research,
        allowed_evidence_ids={"regime"},
        evidence_bundle=_BUNDLE,
    )
    assert qa_st == "FAIL"
    assert any("unsupported_claim:claim:0" in r for r in qa_reasons)
    assert any("revenue" in r and "surged" in r for r in qa_reasons)

    catalog = approved_claim_catalog(
        research,
        allowed_evidence_ids={"regime"},
        evidence_bundle=_BUNDLE,
        qa_output=qa_lie,
    )
    assert catalog == []

    status, reasons = evaluate_final_selector_gate(
        _ids("claim:0"),
        allowed_evidence_ids={"regime"},
        evidence_bundle=_BUNDLE,
        research_output=research,
        qa_output=qa_lie,
    )
    assert status == "FAIL"
    assert any("unknown_claim_ref:claim:0" in r for r in reasons)
    materialized = materialize_final_selector(_ids("claim:0"), catalog)
    assert "revenue" not in materialized["rationale"].lower()
    assert "surged" not in materialized["rationale"].lower()
