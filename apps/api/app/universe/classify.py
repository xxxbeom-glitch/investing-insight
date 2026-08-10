from __future__ import annotations

from dataclasses import dataclass

UNIVERSE_NAME = "us_nyse_nasdaq_equity_v1"
RULE_VERSION = "universe-rules-v0.1"

# Massive ticker type codes
INCLUDE_TYPES = {"CS", "ADRC", "OS", "NYRS"}
EXCLUDE_TYPES = {
    "ETF",
    "ETN",
    "ETV",
    "ETS",
    "PFD",
    "WARRANT",
    "RIGHT",
    "FUND",
    "UNIT",
    "BASKET",
    "BOND",
    "AGEN",
    "EQLK",
    "SP",
    "LT",
    "ADRP",
    "ADRW",
    "ADRR",
    "GDR",
    "OTHER",
}

ALLOWED_EXCHANGES = {"XNYS", "XNAS"}

ADR_TYPES = {"ADRC", "ADRP", "ADRW", "ADRR"}


@dataclass(frozen=True)
class Classification:
    included: bool
    inclusion_reason: str | None
    exclusion_reason: str | None
    is_adr: bool
    exchange: str
    security_type: str


def _name_exclusion(name: str) -> str | None:
    n = f" {name.upper()} "
    if " REIT" in n or "REIT " in n or name.upper().endswith(" REIT"):
        return "name_contains_reit"
    if "REAL ESTATE INVESTMENT TRUST" in name.upper():
        return "name_contains_reit"
    if " BDC " in n or name.upper().endswith(" BDC"):
        return "name_contains_bdc"
    if "BUSINESS DEVELOPMENT COMPANY" in name.upper():
        return "name_contains_bdc"
    if "ACQUISITION CORP" in name.upper() or "ACQUISITION CORPORATION" in name.upper():
        return "name_suggests_spac"
    if " SPAC " in n:
        return "name_suggests_spac"
    return None


def classify_ticker(row: dict) -> Classification:
    ticker = str(row.get("ticker") or "").strip().upper()
    name = str(row.get("name") or "").strip()
    market = str(row.get("market") or "").strip().lower()
    locale = str(row.get("locale") or "").strip().lower()
    exchange = str(row.get("primary_exchange") or "").strip().upper()
    security_type = str(row.get("type") or "").strip().upper() or "UNKNOWN"
    active = bool(row.get("active", True))
    is_adr = security_type in ADR_TYPES or security_type == "ADRC"

    if market and market != "stocks":
        return Classification(False, None, f"market_{market}", is_adr, exchange, security_type)
    if locale and locale not in {"us", ""}:
        # still allow ADR listed on US exchanges
        if exchange not in ALLOWED_EXCHANGES:
            return Classification(False, None, f"locale_{locale}", is_adr, exchange, security_type)
    if not active:
        return Classification(False, None, "inactive", is_adr, exchange, security_type)
    if not ticker:
        return Classification(False, None, "missing_ticker", is_adr, exchange, security_type)
    if exchange not in ALLOWED_EXCHANGES:
        return Classification(False, None, f"exchange_{exchange or 'missing'}", is_adr, exchange, security_type)
    if security_type in EXCLUDE_TYPES:
        return Classification(False, None, f"type_{security_type}", is_adr, exchange, security_type)

    name_reason = _name_exclusion(name)
    if name_reason:
        return Classification(False, None, name_reason, is_adr, exchange, security_type)

    if security_type not in INCLUDE_TYPES:
        return Classification(False, None, f"type_not_allowed_{security_type}", is_adr, exchange, security_type)

    reason = f"type_{security_type}_exchange_{exchange}"
    if is_adr:
        reason += "_adr"
    return Classification(True, reason, None, True if security_type == "ADRC" else is_adr, exchange, security_type)
