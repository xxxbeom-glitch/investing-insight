import pytest

from app.agents.claim_support import ClaimTriple, claim_is_supported, claim_unsupported_tokens, parse_claim
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


def test_true_pair_structures_as_field_equals_value():
    triples, missing = parse_claim("regime is expansion", "regime", _REGIME)
    assert missing == set()
    assert triples == [ClaimTriple(field="regime", operator="equals", value="expansion")]


@pytest.mark.parametrize(
    "text",
    [
        "regime is expansion",
        "regime was expansion",
        "regime were expansion",
        "regime are expansion",
        "regime: expansion",
        "expansion is regime",
        "expansion was regime",
    ],
)
def test_copula_and_orientation_do_not_change_true_pair(text):
    triples, missing = parse_claim(text, "regime", _REGIME)
    assert not missing
    assert any(t.field == "regime" and t.operator == "equals" and t.value == "expansion" for t in triples)
    assert claim_is_supported(text, "regime", _REGIME)


@pytest.mark.parametrize(
    ("text", "eid", "evidence"),
    [
        ("expansion is as_of", "regime", _REGIME),
        ("expansion was as_of", "regime", _REGIME),
        ("expansion are as_of", "regime", _REGIME),
        ("expansion were as_of", "regime", _REGIME),
        ("2026 is close", "price:1", _PRICE),
        ("2026 was close", "price:1", _PRICE),
        ("100.5 is trading_date", "price:1", _PRICE),
        ("100.5 was trading_date", "price:1", _PRICE),
        ("81.32 is overall_score", "assessment:software", _ASSESS),
        ("81.32 are overall_score", "assessment:software", _ASSESS),
        ("demand is 81.32A", "assessment:software", _ASSESS),
        ("demand is 81.32A.", "assessment:software", _ASSESS),
        ("close is 100.5B", "price:1", _PRICE),
        ("regime is 2026-08-10", "regime", _REGIME),
        ("as_of is expansion", "regime", _REGIME),
        ("close is 2026", "price:1", _PRICE),
        ("overall_score 81.32", "assessment:software", _ASSESS),
        ("kind is regime", "regime", _REGIME),
        ("regime is expansion and 매출 급증", "regime", _REGIME),
        ("regime is expansion and 收入暴增", "regime", _REGIME),
        ("regime is expansion and X", "regime", _REGIME),
        ("regime is expansion and revenue surged", "regime", _REGIME),
        ("The CEO resigned yesterday", "regime", _REGIME),
        ("secret-ref close 100.5", "price:1", _PRICE),
        ("kind is daily_price", "price:1", _PRICE),
        ("regime is expansion\x7f.", "regime", _REGIME),
        ("close is 100.5\u200b.", "price:1", _PRICE),
        ("as_of is expansion 2026-08-10", "regime", _REGIME),
    ],
)
def test_generalized_attacks_fail_without_copula_list(text, eid, evidence):
    assert claim_is_supported(text, eid, evidence) is False
    assert claim_unsupported_tokens(text, eid, evidence)


@pytest.mark.parametrize(
    ("text", "eid", "evidence"),
    [
        ("close is 100.5", "price:1", _PRICE),
        ("100.5 is close", "price:1", _PRICE),
        ("close was 100.5", "price:1", _PRICE),
        ("100.5 was close", "price:1", _PRICE),
        ("trading_date is 2026-08-10", "price:1", _PRICE),
        ("2026-08-10 is trading_date", "price:1", _PRICE),
        ("regime is expansion", "regime", _REGIME),
        ("as_of is 2026-08-10", "regime", _REGIME),
        ("regime is expansion as of 2026-08-10", "regime", _REGIME),
        ("overall_score 61.76", "assessment:software", _ASSESS),
        ("software overall_score 61.76", "assessment:software", _ASSESS),
        ("demand score of 81.32", "assessment:software", _ASSESS),
        ("close 100.5", "price:1", _PRICE),
    ],
)
def test_existing_true_claims_still_pass(text, eid, evidence):
    assert claim_is_supported(text, eid, evidence) is True
    assert claim_unsupported_tokens(text, eid, evidence) == set()


def test_token_bag_alone_is_not_support():
    text = "expansion as_of"
    assert claim_is_supported(text, "regime", _REGIME) is False
    missing = claim_unsupported_tokens(text, "regime", _REGIME)
    assert missing


def test_wrapper_and_meta_cannot_ground():
    evidence = [
        {
            "evidence_id": "regime",
            "kind": "regime",
            "leaked_meta": "should-not-count",
        }
    ]
    assert not claim_is_supported("regime is expansion", "regime", evidence)
    assert not claim_is_supported("leaked_meta should-not-count", "regime", evidence)


def test_false_copula_variant_cannot_reach_judgment_even_if_qa_lies():
    research = {
        "claims": [{"claim": "expansion was as_of", "evidence_id": "regime"}],
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
