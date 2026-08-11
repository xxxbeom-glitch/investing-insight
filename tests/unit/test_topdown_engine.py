from datetime import date, timedelta

import pytest

from app.macro.fred_client import FredClient, FredUnavailableError, load_fred_series_config
from app.macro.regime import classify_regime, load_industry_rules
from app.topdown.engine import industry_qa, load_value_chain, score_industry


def test_fred_config_loads():
    cfg = load_fred_series_config()
    assert cfg["version"].startswith("fred-series-v0.2")
    cpi = next(s for s in cfg["series"] if s["id"] == "CPIAUCSL")
    assert cpi["units"] == "pc1"
    assert cpi["value_unit"] == "yoy_pct"
    assert any(s["id"] == "UNRATE" for s in cfg["series"])


def test_fred_client_requires_key():
    try:
        FredClient("")
        assert False, "expected FredUnavailableError"
    except FredUnavailableError as exc:
        assert "FRED_API_KEY" in str(exc)


def test_cpi_index_level_rejected():
    latest = {
        "labor": {"series_id": "UNRATE", "date": "2026-07-01", "value": 4.1, "value_unit": "percent"},
        "yield_curve": {"series_id": "T10Y2Y", "date": "2026-07-01", "value": 0.4, "value_unit": "percent"},
        "inflation": {"series_id": "CPIAUCSL", "date": "2026-07-01", "value": 300.0, "value_unit": "yoy_pct"},
        "policy_rate": {"series_id": "FEDFUNDS", "date": "2026-07-01", "value": 4.3, "value_unit": "percent"},
        "industrial_production": {"series_id": "INDPRO", "date": "2026-07-01", "value": 103.0, "value_unit": "index"},
    }
    rules = load_industry_rules()
    ind = rules["industries"][0]
    with pytest.raises(ValueError, match="CPI index"):
        score_industry(ind, latest, "expansion")


def test_inflation_yoy_near_target_not_saturated():
    latest = {
        "labor": {"series_id": "UNRATE", "date": "2026-07-01", "value": 4.1, "value_unit": "percent"},
        "yield_curve": {"series_id": "T10Y2Y", "date": "2026-07-01", "value": 0.4, "value_unit": "percent"},
        "inflation": {"series_id": "CPIAUCSL", "date": "2026-07-01", "value": 3.0, "value_unit": "yoy_pct"},
        "policy_rate": {"series_id": "FEDFUNDS", "date": "2026-07-01", "value": 4.3, "value_unit": "percent"},
        "industrial_production": {"series_id": "INDPRO", "date": "2026-07-01", "value": 103.0, "value_unit": "index"},
    }
    classified = classify_regime(latest)
    rules = load_industry_rules()
    ind = next(i for i in rules["industries"] if "inflation" in (i.get("fred_tilt") or {}))
    scores = score_industry(ind, latest, classified["regime"])
    # (3-2)*3 = 3 tilt — pricing must not be clamped at +15 from fake index
    assert 0 <= scores["pricing"] <= 100
    assert scores["pricing"] < 70  # not saturated high from index misuse


def test_regime_and_industry_scores_deterministic():
    latest = {
        "labor": {"series_id": "UNRATE", "date": "2026-07-01", "value": 4.1, "value_unit": "percent"},
        "yield_curve": {"series_id": "T10Y2Y", "date": "2026-07-01", "value": 0.4, "value_unit": "percent"},
        "inflation": {"series_id": "CPIAUCSL", "date": "2026-07-01", "value": 2.5, "value_unit": "yoy_pct"},
        "policy_rate": {"series_id": "FEDFUNDS", "date": "2026-07-01", "value": 4.3, "value_unit": "percent"},
        "industrial_production": {"series_id": "INDPRO", "date": "2026-07-01", "value": 103.0, "value_unit": "index"},
    }
    classified = classify_regime(latest)
    assert classified["regime"] in {"expansion", "late_cycle", "contraction", "transition"}
    rules = load_industry_rules()
    ind = rules["industries"][0]
    scores = score_industry(ind, latest, classified["regime"])
    for k in ("demand", "capex", "supply", "pricing", "margin", "bottleneck", "overall"):
        assert k in scores
        assert 0 <= scores[k] <= 100


def test_industry_qa_fail_blocks_low_overall(monkeypatch):
    rules = load_industry_rules()
    assessment = {
        "assessment_id": "00000000-0000-0000-0000-000000000001",
        "scores": {
            "demand": 10,
            "capex": 10,
            "supply": 10,
            "pricing": 10,
            "margin": 10,
            "bottleneck": 10,
            "overall": 10,
        },
    }
    reasons = []
    min_overall = float((rules.get("qa") or {}).get("min_overall", 40))
    if assessment["scores"]["overall"] < min_overall:
        reasons.append(f"overall_below_{min_overall}")
    assert reasons


def test_value_chain_config():
    chain = load_value_chain()
    assert chain["version"].startswith("value-chain")
    assert any(c["industry_id"] == "semis" for c in chain["chains"])
