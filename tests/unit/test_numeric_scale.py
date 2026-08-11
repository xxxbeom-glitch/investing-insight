from decimal import Decimal

from app.research.numeric_scale import (
    iter_quantities,
    packet_absolute_magnitudes,
    phrase_matches_absolute,
    quantity_matches_absolute,
)

ASSETS = Decimal("383266000000")


def test_raw_and_billion_forms_match_same_value():
    assert phrase_matches_absolute("383266000000", ASSETS)
    assert phrase_matches_absolute("$383.266 billion", ASSETS)
    assert phrase_matches_absolute("383.266 billion", ASSETS)
    assert phrase_matches_absolute("383.266B", ASSETS)
    assert phrase_matches_absolute("383,266 million", ASSETS)
    assert phrase_matches_absolute("383.266M", Decimal("383266000"))


def test_wrong_scale_and_value_do_not_match():
    assert phrase_matches_absolute("$384.266 billion", ASSETS) is False
    assert phrase_matches_absolute("$383.266 million", ASSETS) is False
    assert phrase_matches_absolute("383.266%", ASSETS) is False
    assert phrase_matches_absolute("383.266", ASSETS) is False
    assert phrase_matches_absolute("383 billion", ASSETS) is False


def test_percent_is_not_absolute():
    qtys = iter_quantities("383.266%")
    assert len(qtys) == 1
    assert qtys[0].kind == "percent"
    assert quantity_matches_absolute(ASSETS, qtys[0]) is False
    assert quantity_matches_absolute(Decimal("383.266"), qtys[0]) is False


def test_iso_dates_are_not_quantities():
    qtys = iter_quantities("Assets were $383.266 billion at 2026-06-27")
    assert [q.text for q in qtys] == ["$383.266 billion"]
    assert iter_quantities("period_end 2026-06-27") == []


def test_glued_non_unit_letter_is_not_a_quantity():
    assert iter_quantities("demand is 81.32A") == []


def test_negative_and_currency():
    mag = Decimal("-1200000000")
    assert phrase_matches_absolute("-$1.2 billion", mag)
    assert phrase_matches_absolute("-1.2 billion", mag)


def test_packet_reads_string_raw_values_only_from_value_and_close():
    packet = {
        "evidence": [
            {
                "evidence_id": "fact:1",
                "kind": "financial_fact",
                "metric_key": "Assets",
                "value": "383266000000",
                "period_end": "2026-06-27",
                "source_id": "2026",
            }
        ],
        "quant": {"total_score": 88.77},
    }
    mags = packet_absolute_magnitudes(packet)
    assert ASSETS in mags
    assert Decimal("88.77") in mags
    assert Decimal("2026") not in mags


def test_nested_overall_score_is_collected_without_date_fragments():
    packet = {
        "evidence": [
            {
                "evidence_id": "assessment:software",
                "kind": "industry_assessment",
                "payload": {"industry_id": "software", "overall_score": 61.7},
            }
        ],
        "quant": {},
    }
    mags = packet_absolute_magnitudes(packet)
    assert Decimal("61.7") in mags
    assert Decimal("2026") not in mags
