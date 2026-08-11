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
_ASSESS = [
    {
        "evidence_id": "assessment:software",
        "kind": "industry_assessment",
        "payload": {
            "industry_id": "software",
            "overall_score": 61.76,
            "as_of": "2026-08-10",
            "details": {"name": "Software / Platforms", "scores": {"demand": 81.32, "pricing": 54.11}},
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
        ("regime is 2026-08-10", "regime", _REGIME, False),
        ("as_of is expansion", "regime", _REGIME, False),
        ("overall_score 81.32", "assessment:software", _ASSESS, False),
        ("overall score of 81.32", "assessment:software", _ASSESS, False),
        ("close 2026-08-10", "price:1", [{"evidence_id": "price:1", "kind": "daily_price", "trading_date": "2026-08-10", "close": 100.5}], False),
        ("regime is expansion", "regime", _REGIME, True),
        ("regime is expansion as of 2026-08-10", "regime", _REGIME, True),
        ("overall_score 61.76", "assessment:software", _ASSESS, True),
        ("software overall_score 61.76", "assessment:software", _ASSESS, True),
        ("demand score of 81.32", "assessment:software", _ASSESS, True),
        ("close 100.5", "price:1", [{"evidence_id": "price:1", "kind": "daily_price", "trading_date": "2026-08-10", "close": 100.5}], True),
        ("regime is expansion and 매출 급증", "regime", _REGIME, False),
        ("regime is expansion and X", "regime", _REGIME, False),
    ],
)
def test_field_aware_grounding_fixtures(text, eid, evidence, should_pass):
    assert claim_is_supported(text, eid, evidence) is should_pass
    if not should_pass:
        missing = claim_unsupported_tokens(text, eid, evidence)
        assert missing


def test_cross_field_claim_cannot_reach_judgment_even_if_qa_lies():
    research = {
        "claims": [{"claim": "regime is 2026-08-10", "evidence_id": "regime"}],
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
    assert any("field_mismatch:regime" in r for r in qa_reasons)
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
    assert "2026-08-10" not in materialized["rationale"]
