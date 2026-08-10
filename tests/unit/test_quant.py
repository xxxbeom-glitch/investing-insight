from datetime import date

from app.quant.config import load_quant_rules
from app.quant.metrics import (
    cashflow_proxy,
    growth_from_revenues,
    health_from_equity_ratio,
    momentum_from_closes,
    quality_from_roe,
    valuation_from_price_to_book,
    weighted_total,
)
from app.quant.engine import score_security


def test_quant_rules_sum_to_100():
    rules = load_quant_rules()
    assert rules.version == "quant-rules-v0.1"
    assert abs(sum(rules.weights.values()) - 100) < 1e-9


def test_formula_unit_cases():
    assert growth_from_revenues(120, 100)[0] == 70.0
    assert growth_from_revenues(None, 100)[1] is True
    assert quality_from_roe(10, 100)[0] == 60.0
    assert cashflow_proxy(10, 100)[0] == 70.0
    assert health_from_equity_ratio(40, 100)[0] == 40.0
    assert abs(momentum_from_closes([100, 110])[0] - 60.0) < 1e-9
    assert valuation_from_price_to_book(None, 1e9)[1] is True
    total = weighted_total(
        {"growth": 100, "quality": 0, "cashflow": 0, "health": 0, "valuation": 0, "momentum": 0},
        {"growth": 20, "quality": 20, "cashflow": 15, "health": 15, "valuation": 15, "momentum": 15},
    )
    assert total == 20.0


def test_score_security_deterministic():
    rules = load_quant_rules()
    facts = {
        "Revenues": [(date(2024, 12, 31), 120.0), (date(2023, 12, 31), 100.0)],
        "NetIncomeLoss": [(date(2024, 12, 31), 10.0)],
        "StockholdersEquity": [(date(2024, 12, 31), 100.0)],
        "Assets": [(date(2024, 12, 31), 200.0)],
    }
    closes = [(date(2026, 7, 1), 100.0), (date(2026, 7, 2), 105.0)]
    a = score_security(facts_by_metric=facts, closes=closes, rules=rules)
    b = score_security(facts_by_metric=facts, closes=closes, rules=rules)
    assert a == b
    assert a["rule_version"] == rules.version
    assert a["input_hash"]
    assert "total_score" in a
