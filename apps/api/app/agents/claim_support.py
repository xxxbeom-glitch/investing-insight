"""Deterministic claim↔evidence support. Allowed evidence_id is not proof of support."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from app.research.claim_check import _NUM_RE, _norm

# Closed-class function words only. Not a fact denylist — leftover open-class
# tokens (revenue, surged, ceo, …) are unsupported if absent from the payload.
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "with",
}

_WRAPPER_KEYS = {"evidence_id", "kind"}


def claim_text_hash(text: str, evidence_id: str) -> str:
    norm = " ".join(str(text or "").split())
    blob = f"{evidence_id}\n{norm}".encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def content_tokens(text: str) -> set[str]:
    toks = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", str(text or "").lower())
    return {t for t in toks if t not in STOPWORDS and len(t) > 1}


def _payload_blob(item: dict[str, Any]) -> str:
    """Support text is the cited payload only — wrapper keys are not facts."""
    payload = item.get("payload")
    if payload is None:
        payload = {k: v for k, v in item.items() if k not in _WRAPPER_KEYS}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def find_evidence_item(
    evidence: list[Any] | None,
    evidence_id: str,
) -> dict[str, Any] | None:
    eid = str(evidence_id or "").strip()
    for item in evidence or []:
        if isinstance(item, dict) and str(item.get("evidence_id") or "").strip() == eid:
            return item
    return None


def claim_unsupported_tokens(
    claim_text: str,
    evidence_id: str,
    evidence: list[Any] | None,
) -> set[str]:
    """Open-class claim tokens (and numbers) not present in the cited payload."""
    text = str(claim_text or "").strip()
    eid = str(evidence_id or "").strip()
    if not text or not eid:
        return {"empty_claim_or_evidence_id"}
    item = find_evidence_item(evidence, eid)
    if item is None:
        return {"evidence_item_missing"}
    blob = _payload_blob(item)
    missing: set[str] = set()
    ev_nums = {_norm(x) for x in _NUM_RE.findall(blob)}
    for m in _NUM_RE.findall(text):
        if _norm(m) not in ev_nums:
            missing.add(str(m))
    ctoks = content_tokens(text)
    if not ctoks:
        missing.add("no_content_tokens")
        return missing
    missing |= ctoks - content_tokens(blob)
    return missing


def claim_is_supported(
    claim_text: str,
    evidence_id: str,
    evidence: list[Any] | None,
) -> bool:
    """True only if every factual token/number in the claim appears in the cited payload.

    An allowed evidence_id is not enough. Any extra open-class fact fails closed.
    """
    return not claim_unsupported_tokens(claim_text, evidence_id, evidence)


def deterministic_claim_verdicts(
    research_output: dict[str, Any] | None,
    evidence: list[Any] | None,
) -> list[dict[str, str]]:
    verdicts: list[dict[str, str]] = []
    for i, item in enumerate((research_output or {}).get("claims") or []):
        if not isinstance(item, dict):
            cid = f"claim:{i}"
            verdicts.append(
                {
                    "claim_id": cid,
                    "evidence_id": "",
                    "claim_hash": claim_text_hash("", ""),
                    "support": "UNSUPPORTED",
                }
            )
            continue
        text = str(item.get("claim") or "").strip()
        eid = str(item.get("evidence_id") or "").strip()
        cid = f"claim:{i}"
        supported = claim_is_supported(text, eid, evidence)
        verdicts.append(
            {
                "claim_id": cid,
                "evidence_id": eid,
                "claim_hash": claim_text_hash(text, eid),
                "support": "SUPPORTED" if supported else "UNSUPPORTED",
            }
        )
    return verdicts


def verified_claim_ids(verdicts: list[dict[str, str]]) -> list[str]:
    return [v["claim_id"] for v in verdicts if v.get("support") == "SUPPORTED"]
