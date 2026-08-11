"""Deterministic claim↔evidence support. Allowed evidence_id is not proof of support."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from app.research.claim_check import _NUM_RE, _norm

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

# Unsupported qualitative events/actors. Presence in leftover tokens fails closed.
NOVEL_FACT_TOKENS = {
    "acquired",
    "acquisition",
    "arrested",
    "bankrupt",
    "bankruptcy",
    "ceo",
    "cfo",
    "chairman",
    "coo",
    "deceased",
    "defaulted",
    "delisted",
    "died",
    "fired",
    "founder",
    "fraud",
    "indicted",
    "insolvency",
    "insolvent",
    "lawsuit",
    "merger",
    "quit",
    "resignation",
    "resigned",
    "restatement",
    "sued",
    "today",
    "yesterday",
}


def claim_text_hash(text: str, evidence_id: str) -> str:
    norm = " ".join(str(text or "").split())
    blob = f"{evidence_id}\n{norm}".encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def content_tokens(text: str) -> set[str]:
    toks = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", str(text or "").lower())
    return {t for t in toks if t not in STOPWORDS and len(t) > 1}


def _evidence_blob(item: dict[str, Any]) -> str:
    return json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)


def find_evidence_item(
    evidence: list[Any] | None,
    evidence_id: str,
) -> dict[str, Any] | None:
    eid = str(evidence_id or "").strip()
    for item in evidence or []:
        if isinstance(item, dict) and str(item.get("evidence_id") or "").strip() == eid:
            return item
    return None


def claim_is_supported(
    claim_text: str,
    evidence_id: str,
    evidence: list[Any] | None,
) -> bool:
    """True only if the cited evidence payload supports the claim text.

    Numeric tokens in the claim must appear in that evidence item.
    More than half of the claim's content tokens must also appear there.
    Zero-overlap qualitative facts (e.g. CEO resigned vs regime=expansion) fail.
    """
    text = str(claim_text or "").strip()
    eid = str(evidence_id or "").strip()
    if not text or not eid:
        return False
    item = find_evidence_item(evidence, eid)
    if item is None:
        return False
    blob = _evidence_blob(item)
    ev_nums = {_norm(x) for x in _NUM_RE.findall(blob)}
    for m in _NUM_RE.findall(text):
        if _norm(m) not in ev_nums:
            return False
    ctoks = content_tokens(text)
    etoks = content_tokens(blob)
    if not ctoks:
        return False
    overlap = ctoks & etoks
    if not overlap:
        return False
    leftover = ctoks - etoks
    if leftover & NOVEL_FACT_TOKENS:
        return False
    return True


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
