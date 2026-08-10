from __future__ import annotations

from typing import Sequence


def clip_score(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def growth_from_revenues(latest: float | None, prior: float | None, *, neutral: float = 50.0) -> tuple[float, bool]:
    if latest is None or prior is None or prior == 0:
        return float(neutral), True
    growth = (latest - prior) / abs(prior)
    return clip_score(neutral + growth * 100.0), False


def quality_from_roe(net_income: float | None, equity: float | None, *, neutral: float = 50.0) -> tuple[float, bool]:
    if net_income is None or equity is None or equity == 0:
        return float(neutral), True
    roe = net_income / equity
    return clip_score(neutral + roe * 100.0), False


def cashflow_proxy(net_income: float | None, assets: float | None, *, neutral: float = 50.0) -> tuple[float, bool]:
    """MVP proxy: NI / Assets (cash flow statement not in MVP fact set)."""
    if net_income is None or assets is None or assets == 0:
        return float(neutral), True
    return clip_score(neutral + (net_income / assets) * 200.0), False


def health_from_equity_ratio(equity: float | None, assets: float | None, *, neutral: float = 50.0) -> tuple[float, bool]:
    if equity is None or assets is None or assets == 0:
        return float(neutral), True
    return clip_score((equity / assets) * 100.0), False


def valuation_from_price_to_book(
    close: float | None,
    equity: float | None,
    *,
    neutral: float = 50.0,
) -> tuple[float, bool]:
    """Without shares outstanding, use close vs equity magnitude as relative cheapness proxy."""
    if close is None or equity is None or equity <= 0 or close <= 0:
        return float(neutral), True
    # lower close/equity_scale → higher score; equity is absolute $, close is $, scale by 1e9
    ratio = close / (equity / 1e9)
    return clip_score(100.0 - min(ratio, 100.0)), False


def momentum_from_closes(closes: Sequence[float], *, neutral: float = 50.0) -> tuple[float, bool]:
    if len(closes) < 2 or closes[0] == 0:
        return float(neutral), True
    ret = closes[-1] / closes[0] - 1.0
    return clip_score(neutral + ret * 100.0), False


def weighted_total(components: dict[str, float], weights: dict[str, float]) -> float:
    return clip_score(sum(components[k] * (weights[k] / 100.0) for k in weights))
