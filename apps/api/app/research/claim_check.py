from __future__ import annotations

from typing import Any

from app.research.numeric_scale import (
    Quantity,
    _NUM_RE,
    _norm,
    iter_quantities,
    packet_absolute_magnitudes,
    quantity_grounded_in,
)

__all__ = [
    "Quantity",
    "_NUM_RE",
    "_norm",
    "deterministic_qa",
    "find_unsupported_numeric_claims",
]


def _tiny_list_count(qty: Quantity) -> bool:
    return (
        qty.kind == "absolute"
        and qty.scale == 1
        and qty.decimal_places == 0
        and qty.mantissa in {0, 1, 2, 3}
    )


def _qty_fingerprint(qty: Quantity) -> tuple[str, str, str, int]:
    return (qty.kind, str(qty.mantissa), str(qty.scale), qty.decimal_places)


def find_unsupported_numeric_claims(
    packet: dict[str, Any],
    research: dict[str, Any],
) -> list[dict[str, Any]]:
    """Reject numeric claims that are not grounded in packet evidence/quant."""
    allowed = packet_absolute_magnitudes(packet)
    failed: list[dict[str, Any]] = []

    def _row(**kwargs: Any) -> dict[str, str]:
        return {
            "reason": str(kwargs.get("reason") or ""),
            "claim": str(kwargs.get("claim") or ""),
            "evidence_id": str(kwargs.get("evidence_id") or ""),
            "number": str(kwargs.get("number") or ""),
            "field": str(kwargs.get("field") or ""),
        }

    mapped: set[tuple[str, str, str, int]] = set()
    evidence_ids = {
        e.get("evidence_id") for e in (packet.get("evidence") or []) if isinstance(e, dict)
    }

    for item in research.get("claim_evidence_map") or []:
        if not isinstance(item, dict):
            failed.append(_row(reason="claim_evidence_map_item_not_object", claim=str(item)))
            continue
        claim = str(item.get("claim") or "")
        eid = item.get("evidence_id")
        if eid and eid not in evidence_ids:
            failed.append(_row(claim=claim, evidence_id=str(eid), reason="evidence_id_not_in_packet"))
        for qty in iter_quantities(claim):
            mapped.add(_qty_fingerprint(qty))
            if not quantity_grounded_in(qty, allowed):
                failed.append(
                    _row(
                        claim=claim,
                        number=qty.text,
                        reason="numeric_not_in_packet_evidence",
                    )
                )

    text_fields = [
        research.get("summary"),
        research.get("financial_interpretation"),
        research.get("valuation_interpretation"),
    ]
    for field in text_fields:
        if not isinstance(field, str):
            continue
        for qty in iter_quantities(field):
            if _tiny_list_count(qty):
                continue
            if quantity_grounded_in(qty, allowed) or _qty_fingerprint(qty) in mapped:
                continue
            failed.append(
                _row(
                    field="narrative",
                    number=qty.text,
                    reason="unsupported_numeric_in_narrative",
                )
            )
    return failed


def deterministic_qa(
    packet: dict[str, Any],
    research: dict[str, Any],
) -> dict[str, Any]:
    failed = find_unsupported_numeric_claims(packet, research)
    warnings: list[str] = []
    if research.get("unsupported_or_missing"):
        warnings.append("research_declared_unsupported_or_missing")
    if not research.get("bear_case"):
        failed.append(
            {
                "reason": "missing_bear_case",
                "claim": "",
                "evidence_id": "",
                "number": "",
                "field": "bear_case",
            }
        )
    status = "FAIL" if failed else ("PASS_WITH_WARNING" if warnings else "PASS")
    return {
        "status": status,
        "failed_claims": failed,
        "warnings": warnings,
        "required_revisions": [f["reason"] for f in failed if isinstance(f, dict) and "reason" in f],
    }
