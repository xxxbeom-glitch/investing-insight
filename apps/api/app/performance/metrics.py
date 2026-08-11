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
) -> dict[str, Any]:
    """
    prices: sorted ascending (date, close).
    Uses next available price on/after entry_as_of as entry,
    then advances `trading_days` available bars for exit.
    """
    if not prices or trading_days <= 0:
        return {"status": "INCOMPLETE", "reason": "no_prices_or_bad_horizon"}

    # index of first bar on/after entry
    start_idx = None
    for i, (d, _) in enumerate(prices):
        if d >= entry_as_of:
            start_idx = i
            break
    if start_idx is None:
        return {"status": "INCOMPLETE", "reason": "no_entry_price"}

    end_idx = start_idx + trading_days
    if end_idx >= len(prices):
        return {
            "status": "INCOMPLETE",
            "reason": "insufficient_forward_bars",
            "entry_date": prices[start_idx][0],
            "entry_price": prices[start_idx][1],
        }

    entry_date, entry_price = prices[start_idx]
    exit_date, exit_price = prices[end_idx]
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


def thesis_correctness(judgment_status: str, abs_ret: float | None, rules: dict[str, Any]) -> str:
    tr = rules.get("thesis_rules") or {}
    if abs_ret is None:
        return str(tr.get("default") or "inconclusive")
    if judgment_status == "SELECTED":
        if abs_ret > 0:
            return str(tr.get("selected_positive") or "supported")
        if abs_ret < 0:
            return str(tr.get("selected_negative") or "challenged")
    return str(tr.get("default") or "inconclusive")


def cohort_for_status(status: str, rules: dict[str, Any]) -> str:
    if status in (rules.get("tracked_statuses") or []):
        if status == "SELECTED":
            return "selected"
        if status in (rules.get("control_statuses") or []):
            return "control"
        return status.lower()
    return "other"
