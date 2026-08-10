from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any


class DataQAError(ValueError):
    pass


def assert_missing_not_zero(value: Any, *, field: str) -> None:
    """Missing must stay None/absent — never coerced to 0 silently."""
    if value is None:
        return
    # explicit zero is allowed only if present; this guards NaN-like sentinels
    if isinstance(value, float) and value != value:  # NaN
        raise DataQAError(f"{field}: NaN not allowed")


def assert_not_future_date(d: date | None, *, field: str, today: date | None = None) -> None:
    if d is None:
        return
    ref = today or datetime.now(timezone.utc).date()
    if d > ref:
        raise DataQAError(f"{field}: future date {d} > {ref}")


def validate_daily_price_row(row: dict[str, Any], *, today: date | None = None) -> None:
    for f in ("open", "high", "low", "close", "volume"):
        if f not in row or row[f] is None:
            raise DataQAError(f"missing {f}")
        assert_missing_not_zero(row[f], field=f)
    o, h, l, c, v = map(float, (row["open"], row["high"], row["low"], row["close"], row["volume"]))
    if min(o, h, l, c) <= 0:
        raise DataQAError("non-positive price")
    if v < 0:
        raise DataQAError("negative volume")
    if h < l or h < max(o, c) or l > min(o, c):
        raise DataQAError("ohlc invalid")
    td = row.get("trading_date")
    if isinstance(td, str):
        td = date.fromisoformat(td)
    assert_not_future_date(td, field="trading_date", today=today)


def validate_fact_row(row: dict[str, Any], *, today: date | None = None) -> None:
    if row.get("value") is None:
        raise DataQAError("missing value (null != 0)")
    assert_missing_not_zero(row["value"], field="value")
    pe = row.get("period_end")
    pub = row.get("published_at")
    if isinstance(pe, str):
        pe = date.fromisoformat(pe)
    if isinstance(pub, str):
        pub = date.fromisoformat(pub)
    if pe is None:
        raise DataQAError("missing period_end")
    assert_not_future_date(pe, field="period_end", today=today)
    assert_not_future_date(pub, field="published_at", today=today)
