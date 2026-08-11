from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def price_on_or_after(prices: list[tuple[date, float]], target: date) -> tuple[date, float] | None:
    for d, p in prices:
        if d >= target:
            return d, p
    return None


def price_on_or_before(prices: list[tuple[date, float]], target: date) -> tuple[date, float] | None:
    hit = None
    for d, p in prices:
        if d <= target:
            hit = (d, p)
        else:
            break
    return hit


def forward_return(
    prices: list[tuple[date, float]],
    *,
    entry_as_of: date,
    trading_days: int,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    """
    prices: sorted ascending (date, close), already capped to <= as_of_date by caller.
    Uses next available price on/after entry_as_of as entry,
    then advances `trading_days` available bars for exit.
    Exit bar must also be <= as_of_date when provided (ER-P1-04 leakage).
    """
    if not prices or trading_days <= 0:
        return {"status": "INCOMPLETE", "reason": "no_prices_or_bad_horizon"}

    eligible = prices
    if as_of_date is not None:
        eligible = [(d, p) for d, p in prices if d <= as_of_date]
        if not eligible:
            return {"status": "INCOMPLETE", "reason": "no_prices_on_or_before_as_of"}

    start_idx = None
    for i, (d, _) in enumerate(eligible):
        if d >= entry_as_of:
            start_idx = i
            break
    if start_idx is None:
        return {"status": "INCOMPLETE", "reason": "no_entry_price"}

    end_idx = start_idx + trading_days
    if end_idx >= len(eligible):
        return {
            "status": "INCOMPLETE",
            "reason": "insufficient_forward_bars",
            "entry_date": eligible[start_idx][0],
            "entry_price": eligible[start_idx][1],
        }

    entry_date, entry_price = eligible[start_idx]
    exit_date, exit_price = eligible[end_idx]
    if entry_price <= 0:
        return {"status": "INCOMPLETE", "reason": "non_positive_entry"}
    abs_ret = (exit_price / entry_price) - 1.0
    return {
        "status": "COMPLETE",
        "entry_date": entry_date,
        "exit_date": exit_date,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "abs_return": abs_ret,
    }


def relative_return(abs_ret: float | None, bench_ret: float | None) -> float | None:
    if abs_ret is None or bench_ret is None:
        return None
    return abs_ret - bench_ret


def price_outcome(abs_ret: float | None) -> str:
    if abs_ret is None:
        return "unknown"
    if abs_ret > 0:
        return "up"
    if abs_ret < 0:
        return "down"
    return "flat"


def thesis_correctness(
    judgment_status: str,
    abs_ret: float | None,
    rules: dict[str, Any],
    *,
    thesis_driver_eval: str | None = None,
) -> str:
    """Price outcome must not determine thesis correctness (ER-P1-04)."""
    tr = rules.get("thesis_rules") or {}
    if thesis_driver_eval:
        return str(thesis_driver_eval)
    # Explicitly ignore abs_ret / judgment_status price coupling
    _ = (judgment_status, abs_ret)
    return str(tr.get("default") or "UNASSESSED")


def cohort_for_status(status: str, rules: dict[str, Any]) -> str:
    if status in (rules.get("tracked_statuses") or []):
        if status == "SELECTED":
            return "selected"
        if status in (rules.get("control_statuses") or []):
            return "control"
        return status.lower()
    return "other"
