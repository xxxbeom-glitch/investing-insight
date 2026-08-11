"""Shared factual magnitude contract for L08 claim_check and M03 claim_support.

Claim-side absolute units (fail-closed otherwise):
- none (same scale as evidence)
- million / millions / M
- billion / billions / B

'$' is scaffolding. Thousands separators are mantissa punctuation.
Percent is a different kind and never matches absolute evidence.
ISO dates are not quantities. A number glued to a non-unit letter is not a quantity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

_NUM_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?")
_ISO_DATE = re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)")
_HEAD = re.compile(
    r"(?<![A-Za-z0-9])(?P<sign>[-+])?\s*\$?\s*"
    r"(?P<mant>(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?(?:e[-+]?\d+)?))"
)
_UNIT = re.compile(r"(?:billions?|millions?|[bm])(?![a-z])", re.IGNORECASE)
_SCALE = {
    "billion": Decimal("1000000000"),
    "billions": Decimal("1000000000"),
    "b": Decimal("1000000000"),
    "million": Decimal("1000000"),
    "millions": Decimal("1000000"),
    "m": Decimal("1000000"),
}


@dataclass(frozen=True)
class Quantity:
    start: int
    end: int
    kind: str  # "absolute" | "percent"
    mantissa: Decimal
    scale: Decimal
    decimal_places: int
    text: str


def _norm(v: Any) -> str:
    try:
        return f"{float(v):.6g}"
    except (TypeError, ValueError):
        return str(v)


def to_decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _decimal_places(mantissa_src: str) -> int:
    body = mantissa_src.replace(",", "")
    if "e" in body.lower():
        try:
            normalized = Decimal(body).normalize()
        except InvalidOperation:
            return 0
        text = format(normalized, "f")
        if "." in text:
            return len(text.split(".", 1)[1].rstrip("0"))
        return 0
    if "." in body:
        return len(body.split(".", 1)[1])
    return 0


def _in_date(start: int, end: int, dates: list[tuple[int, int]]) -> bool:
    return any(a <= start and end <= b for a, b in dates)


def iter_quantities(text: str) -> list[Quantity]:
    raw = str(text or "")
    folded = raw.casefold()
    dates = [(m.start(), m.end()) for m in _ISO_DATE.finditer(raw)]
    out: list[Quantity] = []
    for match in _HEAD.finditer(raw):
        mant_start, mant_end = match.start("mant"), match.end("mant")
        if _in_date(match.start(), mant_end, dates):
            continue
        rest = folded[mant_end:]
        kind = "absolute"
        scale = Decimal(1)
        consumed = 0
        if rest[:1] == "%":
            kind = "percent"
            consumed = 1
        elif rest[:1].isalpha():
            unit = _UNIT.match(rest)
            if unit is None:
                continue
            kind = "absolute"
            scale = _SCALE[unit.group(0).casefold()]
            consumed = unit.end()
        else:
            spaced = re.match(r"\s+", rest)
            skip = spaced.end() if spaced else 0
            tail = rest[skip:]
            if tail[:1] == "%":
                kind = "percent"
                consumed = skip + 1
            else:
                unit = _UNIT.match(tail)
                if unit is not None:
                    kind = "absolute"
                    scale = _SCALE[unit.group(0).casefold()]
                    consumed = skip + unit.end()
        mant_src = match.group("mant")
        sign = match.group("sign") or ""
        try:
            mantissa = Decimal((sign + mant_src).replace(",", ""))
        except InvalidOperation:
            continue
        end = mant_end + consumed
        out.append(
            Quantity(
                start=match.start(),
                end=end,
                kind=kind,
                mantissa=mantissa,
                scale=scale,
                decimal_places=_decimal_places(mant_src),
                text=raw[match.start() : end],
            )
        )
    return out


def quantity_matches_absolute(evidence: Decimal, qty: Quantity) -> bool:
    if qty.kind != "absolute":
        return False
    scaled = qty.mantissa * qty.scale
    if qty.decimal_places == 0:
        return evidence == scaled
    ulp = qty.scale * (Decimal(10) ** -qty.decimal_places)
    return abs(evidence - scaled) <= (ulp / 2)


def phrase_matches_absolute(phrase: str, evidence_raw: Any) -> bool:
    mag = to_decimal(evidence_raw)
    if mag is None:
        return False
    return any(quantity_matches_absolute(mag, qty) for qty in iter_quantities(phrase))


_SKIP_NUMBER_KEYS = frozenset(
    {
        "evidence_id",
        "kind",
        "ref",
        "period_end",
        "published_at",
        "trading_date",
        "as_of",
        "cutoff_at",
        "created_at",
    }
)


def _skip_number_key(key: str) -> bool:
    raw = str(key or "")
    if raw in _SKIP_NUMBER_KEYS:
        return True
    return raw.endswith("_id") or raw.endswith("_hash")


def _walk_absolute_numbers(obj: Any, key: str = "") -> list[Decimal]:
    if _skip_number_key(key):
        return []
    if isinstance(obj, dict):
        out: list[Decimal] = []
        for child_key, val in obj.items():
            out.extend(_walk_absolute_numbers(val, str(child_key)))
        return out
    if isinstance(obj, list):
        out = []
        for val in obj:
            out.extend(_walk_absolute_numbers(val, key))
        return out
    if isinstance(obj, str) and _ISO_DATE.fullmatch(obj.strip()):
        return []
    mag = to_decimal(obj)
    return [mag] if mag is not None else []


def packet_absolute_magnitudes(packet: dict[str, Any]) -> list[Decimal]:
    out: list[Decimal] = []
    for ev in packet.get("evidence") or []:
        out.extend(_walk_absolute_numbers(ev))
    quant = packet.get("quant") or {}
    if isinstance(quant, dict):
        for val in quant.values():
            mag = to_decimal(val)
            if mag is not None:
                out.append(mag)
    return out


def quantity_grounded_in(qty: Quantity, allowed: Iterable[Decimal]) -> bool:
    if qty.kind != "absolute":
        return False
    return any(quantity_matches_absolute(mag, qty) for mag in allowed)
