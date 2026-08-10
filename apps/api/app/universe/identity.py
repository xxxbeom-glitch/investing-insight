from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.universe.classify import Classification, classify_ticker

NS = uuid.UUID("6f1e2c3a-9b8d-4e5f-a1c2-0d9e8f7a6b5c")


@dataclass(frozen=True)
class Identity:
    company_id: uuid.UUID
    security_id: uuid.UUID
    legal_name: str
    sec_cik: str | None
    ticker: str
    exchange: str
    security_type: str
    is_adr: bool
    classification: Classification


def _norm_cik(cik: str | None) -> str | None:
    if not cik:
        return None
    digits = "".join(ch for ch in str(cik) if ch.isdigit())
    return digits.zfill(10) if digits else None


def build_identity(row: dict) -> Identity:
    classification = classify_ticker(row)
    ticker = str(row.get("ticker") or "").strip().upper()
    name = str(row.get("name") or ticker).strip()
    cik = _norm_cik(row.get("cik"))
    figi = str(row.get("share_class_figi") or row.get("composite_figi") or "").strip()
    exchange = classification.exchange or str(row.get("primary_exchange") or "").strip().upper()

    if cik:
        company_key = f"cik:{cik}"
    elif figi:
        company_key = f"figi:{figi}"
    else:
        company_key = f"name:{name.upper()}"

    security_key = f"{exchange}:{ticker}:{figi or row.get('composite_figi') or ticker}"

    return Identity(
        company_id=uuid.uuid5(NS, company_key),
        security_id=uuid.uuid5(NS, security_key),
        legal_name=name,
        sec_cik=cik,
        ticker=ticker,
        exchange=exchange,
        security_type=classification.security_type,
        is_adr=classification.is_adr,
        classification=classification,
    )
