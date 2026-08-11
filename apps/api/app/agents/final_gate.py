"""Final Selector gate: factual content is claim IDs; text is reconstructed (ER3-P1-01)."""

from __future__ import annotations

from typing import Any

from app.research.claim_check import find_unsupported_numeric_claims


def approved_claim_catalog(
    research_output: dict[str, Any] | None,
    adversarial_output: dict[str, Any] | None = None,
    *,
    allowed_evidence_ids: list[str] | set[str] | None = None,
) -> list[dict[str, str]]:
    """Authoritative catalog: evidence-bound research.claims only.

    synthesis / bear_case / adversarial free text are presentation-only and
    cannot be cited into a persisted judgment.
    """
    del adversarial_output  # not admitted as factual catalog entries
    catalog: list[dict[str, str]] = []
    research = research_output or {}
    allowed = set(allowed_evidence_ids) if allowed_evidence_ids is not None else None
    for i, item in enumerate(research.get("claims") or []):
        if not isinstance(item, dict):
            continue
        text = str(item.get("claim") or "").strip()
        eid = str(item.get("evidence_id") or "").strip()
        if not text or not eid:
            continue
        if allowed is not None and eid not in allowed:
            continue
        catalog.append({"claim_id": f"claim:{i}", "text": text, "evidence_id": eid})
    return catalog


def _norm(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def _id_list(output: dict[str, Any], key: str) -> list[str]:
    return [str(x).strip() for x in (output.get(key) or []) if str(x).strip()]


def materialize_final_selector(
    output: dict[str, Any],
    catalog: list[dict[str, str]],
) -> dict[str, Any]:
    """Authoritative judgment text is reconstructed from cited claim IDs only."""
    by_id = {c["claim_id"]: c["text"] for c in catalog}
    r_ids = _id_list(output, "rationale_claim_refs")
    b_ids = _id_list(output, "bear_case_claim_refs")
    k_ids = _id_list(output, "risks_claim_refs")
    i_ids = _id_list(output, "invalidation_claim_refs")
    if not r_ids:
        r_ids = _id_list(output, "claim_refs")
    out = dict(output)
    out["rationale"] = " ".join(by_id[i] for i in r_ids if i in by_id)
    out["bear_case"] = [by_id[i] for i in b_ids if i in by_id]
    out["risks"] = [by_id[i] for i in k_ids if i in by_id]
    out["invalidation_conditions"] = [by_id[i] for i in i_ids if i in by_id]
    out["rationale_claim_refs"] = r_ids
    out["bear_case_claim_refs"] = b_ids
    out["risks_claim_refs"] = k_ids
    out["invalidation_claim_refs"] = i_ids
    out["claim_refs"] = list(dict.fromkeys(r_ids + b_ids + k_ids + i_ids))
    return out


def _free_text_must_match(
    output: dict[str, Any],
    expected: dict[str, Any],
    reasons: list[str],
) -> None:
    if "rationale" in output and str(output.get("rationale") or "").strip():
        if _norm(str(output.get("rationale"))) != _norm(expected.get("rationale") or ""):
            reasons.append("rationale_not_bound_to_claim_refs")
    for field in ("bear_case", "risks", "invalidation_conditions"):
        if field not in output:
            continue
        got = output.get(field)
        if not got:
            continue
        got_n = [_norm(x) for x in got]
        exp_n = [_norm(x) for x in (expected.get(field) or [])]
        if got_n != exp_n:
            reasons.append(f"{field}_not_bound_to_claim_refs")


def evaluate_final_selector_gate(
    output: dict[str, Any],
    *,
    allowed_evidence_ids: list[str] | set[str],
    evidence_bundle: dict[str, Any] | None = None,
    research_output: dict[str, Any] | None = None,
    adversarial_output: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    allowed = set(allowed_evidence_ids or [])
    reasons: list[str] = []
    status = str(output.get("status") or "").upper()
    refs = list(output.get("evidence_refs") or [])

    for ref in refs:
        if ref not in allowed:
            reasons.append(f"unknown_ref:{ref}")

    catalog = approved_claim_catalog(
        research_output,
        adversarial_output,
        allowed_evidence_ids=allowed,
    )
    by_id = {c["claim_id"]: c for c in catalog}
    r_ids = _id_list(output, "rationale_claim_refs")
    b_ids = _id_list(output, "bear_case_claim_refs")
    k_ids = _id_list(output, "risks_claim_refs")
    i_ids = _id_list(output, "invalidation_claim_refs")
    if not r_ids:
        r_ids = _id_list(output, "claim_refs")

    if catalog and not r_ids:
        reasons.append("missing_claim_refs")

    for cid in r_ids + b_ids + k_ids + i_ids:
        if cid not in by_id:
            reasons.append(f"unknown_claim_ref:{cid}")

    if status == "SELECTED":
        if not b_ids:
            reasons.append("selected_empty_bear_case")
        if not k_ids:
            reasons.append("selected_empty_risks")
        if not i_ids:
            reasons.append("selected_empty_invalidation_conditions")
        if not refs:
            reasons.append("selected_empty_evidence_refs")
        if catalog and not r_ids:
            reasons.append("selected_empty_claim_refs")

    expected = materialize_final_selector(output, catalog)
    _free_text_must_match(output, expected, reasons)

    bundle = evidence_bundle or {}
    packet = {
        "evidence": bundle.get("evidence") or [],
        "quant": bundle.get("quant") or {},
    }
    research = {
        "claim_evidence_map": [
            {"claim": expected.get("rationale") or "", "evidence_id": refs[0] if refs else ""}
        ],
        "summary": expected.get("rationale") or "",
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
