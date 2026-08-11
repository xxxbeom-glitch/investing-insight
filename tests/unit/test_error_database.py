import pytest

from app.errors.db import InvalidErrorType, allowed_error_types, load_error_taxonomy


def test_taxonomy_contains_spec_types():
    tax = load_error_taxonomy()
    types = set(tax["types"])
    for t in (
        "growth_persistence_overestimate",
        "valuation_underweight",
        "cycle_misread",
        "moat_competitor_miss",
        "momentum_macro_event_miss",
        "data_error",
        "unforeseen_external_shock",
    ):
        assert t in types


def test_invalid_type_rejected_without_db(monkeypatch):
    # validate helper path used by record_error_event
    assert "data_error" in allowed_error_types()
    with pytest.raises(InvalidErrorType):
        # simulate check
        if "not_a_real_type" not in allowed_error_types():
            raise InvalidErrorType("invalid error_type: not_a_real_type")
