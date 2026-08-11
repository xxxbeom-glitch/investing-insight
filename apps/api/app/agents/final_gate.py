"""Deterministic Final Selector gate before judgment projection (ER3-P1-01)."""

from __future__ import annotations

import re
from typing import Any

from app.research.claim_check import find_unsupported_numeric_claims

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Interpretive / process vocabulary allowed in Final Selector prose.
# Factual leftovers like insolvent/resigned/cloud-contract are NOT in this set.
_META = {
    "packet", "evidence", "snapshot", "claim", "claims", "thesis", "rationale",
    "however", "therefore", "insufficient", "missing", "specific", "company",
    "sector", "industry", "assessment", "assessments", "regime", "expansion",
    "contraction", "ranked", "highest", "provided", "supplied", "conclusion",
    "observation", "dated", "current", "cannot", "without", "which", "while",
    "among", "supports", "only", "macro", "context", "research", "fundamentals",
    "risks", "risk", "bear", "invalidation", "watch", "selected", "reject",
    "tracking", "gates", "passed", "using", "allowed", "grounded", "ticker",
    "security", "union", "shortlist", "model", "labeled", "conditions",
    "dimension", "operating", "financial", "valuation", "market", "event",
    "forecast", "primary", "material", "performance", "guidance", "balance",
    "sheet", "capital", "product", "execution", "regulatory", "exposure",
    "would", "rely", "unsupported", "extrapolation", "level", "fill", "absence",
    "data", "record", "contains", "connect", "outcomes", "thresholds",
    "historical", "validation", "synchronized", "inputs", "classification",
    "premise", "usefulness", "durability", "methodology", "weighting", "trend",
    "history", "confidence", "measure", "non", "synchronous", "through",
    "limiting", "interpretation", "single", "contemporaneous", "favorable",
    "establish", "margins", "competitive", "position", "future", "derived",
    "disclosed", "predictive", "platforms", "software", "energy", "semis",
    "equip", "demand", "capex", "supply", "pricing", "margin", "bottleneck",
    "overall", "score", "agent", "final", "selector", "status", "because",
    "since", "also", "into", "from", "this", "that", "with", "have", "been",
    "does", "not", "there", "their", "about", "must", "should", "gate",
    "approved", "qa", "adversarial", "refs", "ref", "id", "ids", "none",
    "available", "present", "absent", "limited", "incomplete", "unknown",
    "cannot", "beyond", "scope", "given", "based", "cited", "citing",
    "although", "supplies", "establishes", "reassess", "rejection", "rejected",
    "unless", "until", "whether", "within", "without", "instead", "rather",
    "neither", "either", "nor", "via", "per", "versus", "vs", "etc",
}


def approved_claim_catalog(
    research_output: dict[str, Any] | None,
    adversarial_output: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Immutable IDs for QA-approved research claims and adversarial findings."""
    catalog: list[dict[str, str]] = []
    research = research_output or {}
    for i, item in enumerate(research.get("claims") or []):
        if not isinstance(item, dict):
            continue
        text = str(item.get("claim") or "").strip()
        if not text:
            continue
        catalog.append(
            {
                "claim_id": f"claim:{i}",
                "text": text,
                "evidence_id": str(item.get("evidence_id") or ""),
            }
        )
    for i, text in enumerate(research.get("bear_case") or []):
        t = str(text).strip()
        if t:
            catalog.append({"claim_id": f"research_bear:{i}", "text": t, "evidence_id": ""})
    synth = str(research.get("synthesis") or "").strip()
    if synth:
        catalog.append({"claim_id": "research:synthesis", "text": synth, "evidence_id": ""})
    adv = adversarial_output or {}
    ct = str(adv.get("counter_thesis") or "").strip()
    if ct:
        catalog.append({"claim_id": "adv:counter_thesis", "text": ct, "evidence_id": ""})
    for i, text in enumerate(adv.get("broken_assumptions") or []):
        t = str(text).strip()
        if t:
            catalog.append({"claim_id": f"adv:broken:{i}", "text": t, "evidence_id": ""})
    return catalog


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(str(text or "").lower()))


_FACTUAL_DENY = {
    "insolvent", "insolvency", "bankrupt", "bankruptcy", "resigned", "resignation",
    "defaulted", "ousted", "hacked", "fraud", "lawsuit", "indicted",
}


def _significant(tokens: set[str]) -> set[str]:
    out = set()
    for t in tokens:
        if t in _META:
            continue
        if t.isdigit():
            continue
        if t in _FACTUAL_DENY or len(t) >= 8:
            out.add(t)
    return out


def _corpus_text(evidence_bundle: dict[str, Any] | None, cited_ids: set[str]) -> str:
    parts: list[str] = []
    bundle = evidence_bundle or {}
    for ev in bundle.get("evidence") or []:
        if not isinstance(ev, dict):
            continue
        eid = str(ev.get("evidence_id") or "")
        if cited_ids and eid not in cited_ids:
            continue
        parts.append(eid)
        parts.append(json_blob(ev))
    ticker = str(bundle.get("ticker") or "")
    if ticker:
        parts.append(ticker)
    return " ".join(parts)


def json_blob(obj: Any) -> str:
    if isinstance(obj, dict):
        return " ".join(json_blob(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(json_blob(v) for v in obj)
    return str(obj)


def _final_texts(output: dict[str, Any]) -> list[str]:
    texts = [str(output.get("rationale") or "")]
    for field in ("bear_case", "risks", "invalidation_conditions"):
        for item in output.get(field) or []:
            texts.append(str(item))
    return texts


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

    if status == "SELECTED":
        for field in ("bear_case", "risks", "invalidation_conditions", "evidence_refs"):
            arr = output.get(field) or []
            if not isinstance(arr, list) or not any(str(x).strip() for x in arr):
                reasons.append(f"selected_empty_{field}")

    catalog = approved_claim_catalog(research_output, adversarial_output)
    by_id = {c["claim_id"]: c for c in catalog}
    claim_refs = [str(x) for x in (output.get("claim_refs") or []) if str(x).strip()]
    if catalog and not claim_refs:
        reasons.append("missing_claim_refs")
    for cid in claim_refs:
        if cid not in by_id:
            reasons.append(f"unknown_claim_ref:{cid}")
    if status == "SELECTED" and catalog and not claim_refs:
        reasons.append("selected_empty_claim_refs")

    # QA-approved catalog is the only allowed factual corpus (cited refs must still be valid IDs).
    allowed_tokens = _tokens(" ".join(c["text"] for c in catalog))
    allowed_tokens |= _tokens(_corpus_text(evidence_bundle, set(refs)))
    ticker = str((evidence_bundle or {}).get("ticker") or "")
    if ticker:
        allowed_tokens |= _tokens(ticker)

    for text in _final_texts(output):
        leftover = _significant(_tokens(text) - allowed_tokens)
        if leftover:
            sample = ",".join(sorted(leftover)[:6])
            reasons.append(f"unsupported_factual:{sample}")

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
