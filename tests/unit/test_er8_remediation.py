import pytest

from app.agents.claim_support import claim_is_supported, claim_unsupported_tokens, factual_payload
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


@pytest.mark.parametrize(
    ("text", "should_pass"),
    [
        ("regime is expansion and 매출 급증", False),
        ("regime is expansion and 收入暴增", False),
        ("regime is expansion and X", False),
        ("regime is expansion and revenue surged", False),
        ("regime is expansion", True),
    ],
)
def test_unicode_and_single_char_fixtures(text: str, should_pass: bool):
    evidence = _BUNDLE["evidence"]
    assert claim_is_supported(text, "regime", evidence) is should_pass
    if not should_pass:
        assert claim_unsupported_tokens(text, "regime", evidence)


def test_korean_appended_fact_cannot_reach_judgment_even_if_qa_lies():
    research = {
        "claims": [{"claim": "regime is expansion and 매출 급증", "evidence_id": "regime"}],
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
    assert "매출" not in materialized["rationale"]
    assert "급증" not in materialized["rationale"]


def test_wrapper_keys_are_not_support_evidence():
    evidence = _BUNDLE["evidence"]
    assert not claim_is_supported("kind is regime", "regime", evidence)
    assert "kind" in claim_unsupported_tokens("kind is regime", "regime", evidence)


def test_missing_payload_does_not_treat_top_level_wrapper_as_facts():
    evidence = [
        {
            "evidence_id": "regime",
            "kind": "regime",
            "leaked_meta": "should-not-count",
        }
    ]
    assert factual_payload(evidence[0]) == {}
    assert not claim_is_supported("regime is expansion", "regime", evidence)
    assert not claim_is_supported("leaked_meta should-not-count", "regime", evidence)


def test_flattened_daily_price_uses_only_declared_factual_fields():
    evidence = [
        {
            "evidence_id": "price:1",
            "kind": "daily_price",
            "ref": "secret-ref",
            "trading_date": "2026-08-10",
            "close": 100.5,
        }
    ]
    assert factual_payload(evidence[0]) == {"trading_date": "2026-08-10", "close": 100.5}
    assert claim_is_supported("close 100.5", "price:1", evidence)
    assert not claim_is_supported("secret-ref close 100.5", "price:1", evidence)
    assert not claim_is_supported("kind is daily_price", "price:1", evidence)
