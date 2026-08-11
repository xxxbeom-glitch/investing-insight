"""Deterministic Final Selector gate before judgment projection (ER2-P1-02)."""

from __future__ import annotations

from typing import Any

from app.research.claim_check import find_unsupported_numeric_claims


def evaluate_final_selector_gate(
    output: dict[str, Any],
    *,
    allowed_evidence_ids: list[str] | set[str],
    evidence_bundle: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    allowed = set(allowed_evidence_ids or [])
    reasons: list[str] = []
    status = str(output.get("status") or "").upper()
    refs = list(output.get("evidence_refs") or [])

    for ref in refs:
        if ref not in allowed:
            reasons.append(f"unknown_ref:{ref}")

    if status == "SELECTED":
        for field in ("bear_case", "risks", "invalidation_conditions", "evidence_refs"):
            arr = output.get(field) or []
            if not isinstance(arr, list) or not any(str(x).strip() for x in arr):
                reasons.append(f"selected_empty_{field}")

    bundle = evidence_bundle or {}
    packet = {
        "evidence": bundle.get("evidence") or [],
        "quant": bundle.get("quant") or {},
    }
    research = {
        "claim_evidence_map": [{"claim": str(output.get("rationale") or ""), "evidence_id": refs[0] if refs else ""}],
        "summary": str(output.get("rationale") or ""),
        "financial_interpretation": "",
        "valuation_interpretation": "",
    }
    for fail in find_unsupported_numeric_claims(packet, research):
        if fail.get("reason") == "evidence_id_not_in_packet" and not refs:
            continue
        if fail.get("reason") in {"unsupported_numeric_in_narrative", "numeric_not_in_packet_evidence"}:
            reasons.append(f"unsupported_numeric:{fail.get('number')}")

    if reasons:
        return "FAIL", reasons
    return "PASS", []
