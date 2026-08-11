import pytest

from app.agents.claim_support import claim_is_supported, claim_unsupported_tokens
from app.agents.final_gate import (
    approved_claim_catalog,
    evaluate_final_selector_gate,
    materialize_final_selector,
)
from app.agents.runner import evaluate_research_qa_gate

_REGIME = [
    {
        "evidence_id": "regime",
        "kind": "regime",
        "payload": {"regime": "expansion", "as_of": "2026-08-10"},
    }
]
_PRICE = [
    {
        "evidence_id": "price:1",
        "kind": "daily_price",
        "trading_date": "2026-08-10",
        "close": 100.5,
    }
]
_ASSESS = [
    {
        "evidence_id": "assessment:software",
        "kind": "industry_assessment",
        "payload": {
            "industry_id": "software",
            "overall_score": 61.76,
            "details": {"scores": {"demand": 81.32}},
        },
    }
]
_BUNDLE = {"ticker": "MSFT", "evidence": _REGIME}


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


@pytest.mark.parametrize(
    ("text", "eid", "evidence", "should_pass"),
    [
        ("expansion is as_of", "regime", _REGIME, False),
        ("2026 is close", "price:1", _PRICE, False),
        ("100.5 is trading_date", "price:1", _PRICE, False),
        ("81.32 is overall_score", "assessment:software", _ASSESS, False),
        ("close is 100.5", "price:1", _PRICE, True),
        ("100.5 is close", "price:1", _PRICE, True),
        ("trading_date is 2026-08-10", "price:1", _PRICE, True),
        ("2026-08-10 is trading_date", "price:1", _PRICE, True),
        ("regime is expansion", "regime", _REGIME, True),
        ("close is 2026", "price:1", _PRICE, False),
        ("2026 is close", "price:1", _PRICE, False),
    ],
)
def test_direction_free_field_value_relations(text, eid, evidence, should_pass):
    assert claim_is_supported(text, eid, evidence) is should_pass
    if not should_pass:
        assert claim_unsupported_tokens(text, eid, evidence)


def test_reversed_false_pair_cannot_reach_judgment_even_if_qa_lies():
    research = {
        "claims": [{"claim": "expansion is as_of", "evidence_id": "regime"}],
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
    assert "as_of" not in materialized["rationale"]
    assert "expansion" not in materialized["rationale"]
