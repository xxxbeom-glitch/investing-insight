from datetime import date

import pytest

from app.qa.validate import DataQAError, validate_daily_price_row, validate_fact_row


def test_missing_value_not_zero():
    with pytest.raises(DataQAError, match="missing value"):
        validate_fact_row({"value": None, "period_end": "2024-01-01"})


def test_future_date_rejected():
    with pytest.raises(DataQAError, match="future"):
        validate_daily_price_row(
            {"open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "trading_date": "2099-01-01"},
            today=date(2026, 8, 10),
        )


def test_valid_rows_pass():
    validate_daily_price_row(
        {"open": 1, "high": 2, "low": 1, "close": 1.5, "volume": 10, "trading_date": "2026-07-01"},
        today=date(2026, 8, 10),
    )
    validate_fact_row({"value": 0, "period_end": "2024-01-01", "published_at": "2024-02-01"}, today=date(2026, 8, 10))
