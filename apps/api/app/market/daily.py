from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from app.providers.massive import MassiveClient


class MarketDataError(RuntimeError):
    pass


def fetch_daily_bars(
    client: MassiveClient,
    ticker: str,
    start: str,
    end: str,
    *,
    adjusted: bool = True,
) -> list[dict[str, Any]]:
    """Fetch 1-day aggregates. Fail closed on HTTP/provider errors."""
    data = client.get_daily_aggs(ticker, start, end, adjusted=adjusted)
    status = str(data.get("status") or "")
    if status.upper() in {"ERROR", "NOT_FOUND"}:
        raise MarketDataError(f"massive aggregates status={status}")
    results = data.get("results")
    if results is None:
        raise MarketDataError("massive aggregates missing results")
    if not isinstance(results, list):
        raise MarketDataError("massive aggregates results not a list")
    return list(results)


def ms_to_date(ms: int) -> date:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date()


def normalize_bar(raw: dict[str, Any]) -> dict[str, Any]:
    required = ("o", "h", "l", "c", "v", "t")
    for k in required:
        if k not in raw:
            raise MarketDataError(f"bar missing field {k}")
    o, h, l, c, v = (float(raw["o"]), float(raw["h"]), float(raw["l"]), float(raw["c"]), float(raw["v"]))
    if min(o, h, l, c) <= 0:
        raise MarketDataError("non-positive price")
    if v < 0:
        raise MarketDataError("negative volume")
    if h < max(o, c) or l > min(o, c) or h < l:
        raise MarketDataError("ohlc bounds invalid")
    return {
        "trading_date": ms_to_date(int(raw["t"])),
        "open": o,
        "high": h,
        "low": l,
        "close": c,
        "volume": v,
        "adjusted_close": c,
        "vwap": float(raw["vw"]) if raw.get("vw") is not None else None,
        "transactions": int(raw["n"]) if raw.get("n") is not None else None,
    }
