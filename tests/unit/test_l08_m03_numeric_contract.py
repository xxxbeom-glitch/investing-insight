"""Same factual magnitude must not diverge between L08 bag check and M03 triples.

M03 still requires a field token (`value`). Biweekly prose (`Assets were …`) is L08's
shape; that path is covered in test_claim_check.py. Do not treat metric_key display
text as a field — that is outside this numeric-scale fix.
"""

from app.agents.claim_support import claim_is_supported
from app.research.claim_check import find_unsupported_numeric_claims
from app.research.numeric_scale import phrase_matches_absolute

_FACT = [
    {
        "evidence_id": "fact:assets",
        "kind": "financial_fact",
        "metric_key": "Assets",
        "value": "383266000000",
        "period_end": "2026-06-27",
        "source_id": "src",
        "published_at": "2026-07-01",
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


def _l08_numeric_ok(claim: str, packet_evidence: list) -> bool:
    research = {
        "summary": "See evidence",
        "bear_case": ["competition"],
        "claim_evidence_map": [{"claim": claim, "evidence_id": packet_evidence[0]["evidence_id"]}],
        "unsupported_or_missing": [],
    }
    failed = find_unsupported_numeric_claims({"evidence": packet_evidence, "quant": {}}, research)
    return not any(f.get("reason") == "numeric_not_in_packet_evidence" for f in failed)


def test_scaled_raw_pair_supported_on_both_paths():
    l08_claim = "Assets were $383.266 billion at 2026-06-27."
    m03_claim = "value was $383.266 billion"
    assert phrase_matches_absolute("$383.266 billion", "383266000000")
    assert _l08_numeric_ok(l08_claim, _FACT)
    assert _l08_numeric_ok(m03_claim, _FACT)
    assert claim_is_supported(m03_claim, "fact:assets", _FACT) is True


def test_wrong_scale_unsupported_on_both_paths():
    claim = "value was $383.266 million"
    assert _l08_numeric_ok(claim, _FACT) is False
    assert claim_is_supported(claim, "fact:assets", _FACT) is False


def test_wrong_value_unsupported_on_both_paths():
    claim = "value was $384.266 billion"
    assert _l08_numeric_ok(claim, _FACT) is False
    assert claim_is_supported(claim, "fact:assets", _FACT) is False


def test_percent_unsupported_on_both_paths():
    claim = "value was 383.266%"
    assert _l08_numeric_ok(claim, _FACT) is False
    assert claim_is_supported(claim, "fact:assets", _FACT) is False


def test_m03_close_100_5B_stays_unsupported():
    assert claim_is_supported("close is 100.5B", "price:1", _PRICE) is False
    assert _l08_numeric_ok("close is 100.5B", _PRICE) is False
