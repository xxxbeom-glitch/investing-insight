from datetime import date, timedelta

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
    assert rules["version"].startswith("performance-rules-v0.2")
    assert rules["horizons"]["1M"] == 21
    assert "SPY" in rules["benchmarks"]
    assert rules.get("sector_benchmark") == "deferred_until_sector_tag"


def test_forward_return_complete():
    prices = [(date(2026, 1, 1) + timedelta(days=i), 100.0 + i) for i in range(40)]
    out = forward_return(prices, entry_as_of=date(2026, 1, 5), trading_days=21)
    assert out["status"] == "COMPLETE"
    assert out["abs_return"] is not None


def test_forward_return_incomplete_without_fake():
    prices = [(date(2026, 1, 1), 10.0), (date(2026, 1, 2), 11.0)]
    out = forward_return(prices, entry_as_of=date(2026, 1, 1), trading_days=21)
    assert out["status"] == "INCOMPLETE"
    assert "abs_return" not in out or out.get("abs_return") is None


def test_as_of_caps_exit_bar_no_leakage():
    # 100 calendar days of prices, but as_of cuts at day 10 → cannot complete 21-bar horizon
    prices = [(date(2026, 1, 1) + timedelta(days=i), 100.0 + i) for i in range(100)]
    as_of = date(2026, 1, 10)
    out = forward_return(
        prices, entry_as_of=date(2026, 1, 1), trading_days=21, as_of_date=as_of
    )
    assert out["status"] == "INCOMPLETE"
    assert out["reason"] == "insufficient_forward_bars"
    # Without as_of would be COMPLETE — prove leakage is blocked
    full = forward_return(prices, entry_as_of=date(2026, 1, 1), trading_days=21)
    assert full["status"] == "COMPLETE"
    assert full["exit_date"] > as_of


def test_relative_price_and_thesis_decoupled():
    assert relative_return(0.10, 0.02) == 0.08
    assert relative_return(0.10, None) is None
    rules = load_performance_rules()
    # Positive SELECTED return must NOT auto-mark thesis supported
    assert thesis_correctness("SELECTED", 0.05, rules) == "UNASSESSED"
    assert thesis_correctness("SELECTED", -0.05, rules) == "UNASSESSED"
    assert thesis_correctness("WATCH", 0.05, rules) == "UNASSESSED"
    assert price_outcome(0.01) == "up"
    assert price_outcome(-0.01) == "down"
    assert cohort_for_status("WATCH", rules) == "control"
    assert cohort_for_status("SELECTED", rules) == "selected"
