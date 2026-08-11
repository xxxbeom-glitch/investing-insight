from datetime import date

from app.performance.config import load_performance_rules
from app.performance.metrics import (
    cohort_for_status,
    forward_return,
    price_outcome,
    relative_return,
    thesis_correctness,
)


def test_load_performance_rules():
    rules = load_performance_rules()
    assert rules["horizons"]["1M"] == 21
    assert "SPY" in rules["benchmarks"]


def test_forward_return_complete():
    prices = [(date(2026, 1, 1) + __import__("datetime").timedelta(days=i), 100.0 + i) for i in range(40)]
    out = forward_return(prices, entry_as_of=date(2026, 1, 5), trading_days=21)
    assert out["status"] == "COMPLETE"
    assert out["abs_return"] is not None


def test_forward_return_incomplete_without_fake():
    prices = [(date(2026, 1, 1), 10.0), (date(2026, 1, 2), 11.0)]
    out = forward_return(prices, entry_as_of=date(2026, 1, 1), trading_days=21)
    assert out["status"] == "INCOMPLETE"
    assert "abs_return" not in out or out.get("abs_return") is None


def test_relative_and_thesis():
    assert relative_return(0.10, 0.02) == 0.08
    assert relative_return(0.10, None) is None
    rules = load_performance_rules()
    assert thesis_correctness("SELECTED", 0.05, rules) == "supported"
    assert thesis_correctness("SELECTED", -0.05, rules) == "challenged"
    assert thesis_correctness("WATCH", 0.05, rules) == "inconclusive"
    assert price_outcome(0.01) == "up"
    assert cohort_for_status("WATCH", rules) == "control"
    assert cohort_for_status("SELECTED", rules) == "selected"
