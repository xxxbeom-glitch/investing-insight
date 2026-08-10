import json
from pathlib import Path

from app.providers.massive import stable_raw_hash
from app.universe.classify import classify_ticker
from app.universe.identity import build_identity

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "universe_tickers.json"


def _rows():
    return json.loads(FIX.read_text(encoding="utf-8"))


def test_nyse_nasdaq_cs_included():
    rows = {r["ticker"]: classify_ticker(r) for r in _rows()}
    assert rows["AAPL"].included and rows["AAPL"].exchange == "XNAS"
    assert rows["IBM"].included and rows["IBM"].exchange == "XNYS"


def test_adr_included():
    c = classify_ticker(next(r for r in _rows() if r["ticker"] == "BABA"))
    assert c.included
    assert c.is_adr


def test_exclusion_leakage_zero():
    excluded_tickers = {"SPY", "VXX", "PREFER", "WRNT", "VNQ", "O", "DEAD"}
    for row in _rows():
        c = classify_ticker(row)
        if row["ticker"] in excluded_tickers:
            assert not c.included, row["ticker"]
            assert c.exclusion_reason


def test_exclusion_reason_present():
    for row in _rows():
        c = classify_ticker(row)
        if not c.included:
            assert c.exclusion_reason
            assert c.inclusion_reason is None
        else:
            assert c.inclusion_reason
            assert c.exclusion_reason is None


def test_identity_stable_and_unique():
    rows = _rows()
    ids = [build_identity(r) for r in rows]
    sec_ids = [i.security_id for i in ids]
    assert len(sec_ids) == len(set(sec_ids))
    again = build_identity(rows[0])
    assert again.security_id == ids[0].security_id
    assert again.company_id == ids[0].company_id


def test_raw_hash_stable():
    row = _rows()[0]
    assert stable_raw_hash(row) == stable_raw_hash(dict(row))
