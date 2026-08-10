from app.research.claim_check import deterministic_qa, find_unsupported_numeric_claims


def _packet():
    return {
        "evidence": [
            {"evidence_id": "fact:1", "kind": "financial_fact", "value": 100, "metric_key": "Revenues"},
            {"evidence_id": "price:1", "kind": "daily_price", "close": 50},
        ],
        "quant": {"total_score": 61.5},
    }


def test_unsupported_numeric_claim_rejected():
    research = {
        "summary": "Revenue will be 999999 next year",
        "bear_case": ["risk"],
        "claim_evidence_map": [{"claim": "magic number 424242", "evidence_id": "fact:missing"}],
        "unsupported_or_missing": [],
    }
    failed = find_unsupported_numeric_claims(_packet(), research)
    assert any(f.get("reason") == "evidence_id_not_in_packet" for f in failed)
    assert any(f.get("reason") == "numeric_not_in_packet_evidence" for f in failed)
    qa = deterministic_qa(_packet(), research)
    assert qa["status"] == "FAIL"


def test_grounded_claim_can_pass():
    research = {
        "summary": "See evidence",
        "bear_case": ["competition"],
        "claim_evidence_map": [{"claim": "Revenue 100", "evidence_id": "fact:1"}],
        "unsupported_or_missing": ["filings"],
    }
    qa = deterministic_qa(_packet(), research)
    assert qa["status"] in {"PASS", "PASS_WITH_WARNING"}
    assert qa["status"] != "FAIL"
