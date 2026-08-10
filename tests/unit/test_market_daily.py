import pytest

from app.market.daily import MarketDataError, normalize_bar


def test_normalize_bar_ok():
    bar = normalize_bar({"o": 10, "h": 12, "l": 9, "c": 11, "v": 1000, "t": 1704067200000})
    assert bar["open"] == 10
    assert str(bar["trading_date"]) == "2024-01-01" or bar["trading_date"].isoformat().startswith("2024")


def test_normalize_rejects_bad_ohlc():
    with pytest.raises(MarketDataError):
        normalize_bar({"o": 10, "h": 9, "l": 8, "c": 11, "v": 1, "t": 1704067200000})


def test_normalize_rejects_missing():
    with pytest.raises(MarketDataError):
        normalize_bar({"o": 1, "h": 1, "l": 1, "c": 1, "v": 1})
