from __future__ import annotations

import re
from typing import Any


_NUM_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?")


def _evidence_numbers(packet: dict[str, Any]) -> set[str]:
    nums: set[str] = set()
    for ev in packet.get("evidence") or []:
        for key in ("close", "value"):
            if key in ev and ev[key] is not None:
                nums.add(_norm(ev[key]))
        blob = str(ev)
        for m in _NUM_RE.findall(blob):
            nums.add(_norm(m))
    quant = packet.get("quant") or {}
    for v in quant.values():
        if isinstance(v, (int, float)):
            nums.add(_norm(v))
    return nums


def _norm(v: Any) -> str:
    try:
        return f"{float(v):.6g}"
    except (TypeError, ValueError):
        return str(v)


def find_unsupported_numeric_claims(
    packet: dict[str, Any],
    research: dict[str, Any],
) -> list[dict[str, Any]]:
    """Reject numeric claims that are not grounded in packet evidence/quant."""
    allowed = _evidence_numbers(packet)
    failed: list[dict[str, Any]] = []

    for item in research.get("claim_evidence_map") or []:
        if not isinstance(item, dict):
            failed.append({"reason": "claim_evidence_map_item_not_object", "item": item})
            continue
        claim = str(item.get("claim") or "")
        eid = item.get("evidence_id")
        evidence_ids = {e.get("evidence_id") for e in (packet.get("evidence") or []) if isinstance(e, dict)}
        if eid and eid not in evidence_ids:
            failed.append({"claim": claim, "evidence_id": eid, "reason": "evidence_id_not_in_packet"})
        for m in _NUM_RE.findall(claim):
            if _norm(m) not in allowed:
                failed.append(
                    {
                        "claim": claim,
                        "number": m,
                        "reason": "numeric_not_in_packet_evidence",
                    }
                )

    # scan free-text fields for invented absolute numbers with no map entry
    mapped_nums = set()
    for item in research.get("claim_evidence_map") or []:
        if isinstance(item, dict):
            for m in _NUM_RE.findall(str(item.get("claim") or "")):
                mapped_nums.add(_norm(m))

    text_fields = [
        research.get("summary"),
        research.get("financial_interpretation"),
        research.get("valuation_interpretation"),
    ]
    for field in text_fields:
        if not isinstance(field, str):
            continue
        for m in _NUM_RE.findall(field):
            n = _norm(m)
            if n not in allowed and n not in mapped_nums:
                # ignore tiny integers that look like list counts (1-3) optionally
                if n in {"0", "1", "2", "3"}:
                    continue
                failed.append(
                    {
                        "field": "narrative",
                        "number": m,
                        "reason": "unsupported_numeric_in_narrative",
                    }
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
        failed.append({"reason": "missing_bear_case"})
    status = "FAIL" if failed else ("PASS_WITH_WARNING" if warnings else "PASS")
    return {
        "status": status,
        "failed_claims": failed,
        "warnings": warnings,
        "required_revisions": [f["reason"] for f in failed if isinstance(f, dict) and "reason" in f],
    }
