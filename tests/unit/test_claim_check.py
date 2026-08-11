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


def _aapl_assets_packet(**extra):
    evidence = [
        {
            "evidence_id": "fact:assets",
            "kind": "financial_fact",
            "metric_key": "Assets",
            "value": "383266000000",
            "period_end": "2026-06-27",
        }
    ]
    evidence.extend(extra.get("evidence", []))
    return {"evidence": evidence, "quant": {"total_score": 88.77}}


def _map(*claims: str, eid: str = "fact:assets"):
    return {
        "summary": "See evidence",
        "bear_case": ["competition"],
        "claim_evidence_map": [{"claim": c, "evidence_id": eid} for c in claims],
        "unsupported_or_missing": [],
    }


def test_aapl_billion_claims_match_string_raw_value():
    packet = _aapl_assets_packet()
    research = _map(
        "Assets were $383.266 billion at 2026-06-27.",
        "Assets were $383.266 billion",
    )
    failed = find_unsupported_numeric_claims(packet, research)
    assert failed == []
    assert deterministic_qa(packet, research)["status"] != "FAIL"


def test_aapl_live_six_claims_match_their_raw_values():
    packet = {
        "evidence": [
            {"evidence_id": "fact:a", "kind": "financial_fact", "metric_key": "Assets", "value": "383266000000", "period_end": "2026-06-27"},
            {"evidence_id": "fact:e", "kind": "financial_fact", "metric_key": "StockholdersEquity", "value": "107520000000", "period_end": "2026-06-27"},
            {"evidence_id": "fact:n", "kind": "financial_fact", "metric_key": "NetIncomeLoss", "value": "101464000000", "period_end": "2026-06-27"},
            {"evidence_id": "fact:a2", "kind": "financial_fact", "metric_key": "Assets", "value": "359241000000", "period_end": "2025-09-27"},
            {"evidence_id": "fact:e2", "kind": "financial_fact", "metric_key": "StockholdersEquity", "value": "73733000000", "period_end": "2025-09-27"},
            {"evidence_id": "fact:n2", "kind": "financial_fact", "metric_key": "NetIncomeLoss", "value": "112010000000", "period_end": "2025-09-27"},
        ],
        "quant": {},
    }
    research = {
        "summary": "See evidence",
        "bear_case": ["competition"],
        "claim_evidence_map": [
            {"claim": "Assets were $383.266 billion at 2026-06-27.", "evidence_id": "fact:a"},
            {"claim": "Stockholders' equity was $107.520 billion at 2026-06-27.", "evidence_id": "fact:e"},
            {"claim": "Reported NetIncomeLoss was $101.464 billion at 2026-06-27.", "evidence_id": "fact:n"},
            {"claim": "Assets were $359.241 billion at 2025-09-27.", "evidence_id": "fact:a2"},
            {"claim": "Stockholders' equity was $73.733 billion at 2025-09-27.", "evidence_id": "fact:e2"},
            {"claim": "Reported NetIncomeLoss was $112.010 billion at 2025-09-27.", "evidence_id": "fact:n2"},
        ],
        "unsupported_or_missing": [],
    }
    assert find_unsupported_numeric_claims(packet, research) == []
    assert deterministic_qa(packet, research)["status"] != "FAIL"


def test_wrong_billion_value_is_unsupported():
    failed = find_unsupported_numeric_claims(
        _aapl_assets_packet(), _map("Assets were $384.266 billion")
    )
    assert any(f.get("reason") == "numeric_not_in_packet_evidence" for f in failed)


def test_million_scale_does_not_match_billion_raw():
    failed = find_unsupported_numeric_claims(
        _aapl_assets_packet(), _map("Assets were $383.266 million")
    )
    assert any(f.get("reason") == "numeric_not_in_packet_evidence" for f in failed)


def test_percent_does_not_match_absolute_raw():
    failed = find_unsupported_numeric_claims(
        _aapl_assets_packet(), _map("Assets were 383.266%")
    )
    assert any(f.get("reason") == "numeric_not_in_packet_evidence" for f in failed)


def test_date_digits_are_not_financial_values():
    failed = find_unsupported_numeric_claims(
        _aapl_assets_packet(), _map("Assets were 2026")
    )
    assert any(f.get("reason") == "numeric_not_in_packet_evidence" for f in failed)


def test_cross_value_other_metric_is_not_a_free_pass():
    packet = _aapl_assets_packet()
    failed = find_unsupported_numeric_claims(
        packet, _map("Stockholders' equity was $107.520 billion", eid="fact:assets")
    )
    assert any(f.get("reason") == "numeric_not_in_packet_evidence" for f in failed)
