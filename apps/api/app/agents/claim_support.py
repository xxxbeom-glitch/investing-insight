"""Deterministic claim↔evidence support. Allowed evidence_id is not proof of support."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from app.research.claim_check import _NUM_RE, _norm

# Closed-class function words only. Not a fact denylist.
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

# Identity / envelope fields — never support text (load_evidence_bundle).
_WRAPPER_KEYS = frozenset({"evidence_id", "kind", "ref"})

# Lineage / row ids inside payload — not factual support.
_ID_KEYS = frozenset(
    {
        "assessment_id",
        "regime_id",
        "run_id",
        "security_id",
        "union_id",
        "snapshot_id",
        "company_id",
        "error_id",
        "proposal_id",
        "multi_agent_run_id",
        "output_id",
        "job_id",
        "gate_id",
        "input_hash",
    }
)
_SKIP_LEAF_KEYS = _WRAPPER_KEYS | _ID_KEYS

# Flattened items that omit `payload`. Only these keys are factual.
# See apps/api/app/agents/evidence.py load_evidence_bundle.
_KIND_FACTUAL_FIELDS: dict[str, tuple[str, ...]] = {
    "daily_price": ("trading_date", "close"),
    "financial_fact": ("metric_key", "value", "period_end", "published_at", "source_id"),
}

# Numbers first so 61.76 stays one token; then Unicode letters (any script).
_TOKEN_RE = re.compile(r"[0-9]+(?:\.[0-9]+)?|[^\W\d_]+", re.UNICODE)
_COPULA_RE = re.compile(
    r"(?P<field>[^\W\d_]+(?:[_\s/-]+[^\W\d_]+)*)\s+(?:is|:)\s+(?P<neg>not\s+)?"
    r"(?P<value>.+?)(?=\s+(?:and|,|;)\s+|\s+as\s+of\b|$)",
    re.UNICODE | re.IGNORECASE,
)
_NUM_PAT = r"[0-9]+(?:\.[0-9]+)?"


def claim_text_hash(text: str, evidence_id: str) -> str:
    norm = " ".join(str(text or "").split())
    blob = f"{evidence_id}\n{norm}".encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def content_tokens(text: str) -> set[str]:
    """Open-class tokens: Unicode letters (incl. CJK) and numbers. Length-1 kept."""
    folded = str(text or "").casefold()
    return {t for t in _TOKEN_RE.findall(folded) if t not in STOPWORDS}


def factual_payload(item: dict[str, Any]) -> Any:
    """Cited facts only. Wrapper keys and unknown top-level leftovers are not facts."""
    kind = str(item.get("kind") or "")
    fields = _KIND_FACTUAL_FIELDS.get(kind)
    if fields is not None:
        return {k: item[k] for k in fields if k in item}
    if "payload" not in item:
        return {}
    payload = item.get("payload")
    if isinstance(payload, dict):
        return {k: v for k, v in payload.items() if k not in _WRAPPER_KEYS}
    return payload


def _leaf_key(path: str) -> str:
    return path.split(".")[-1]


def _key_tokens(leaf: str) -> set[str]:
    spaced = content_tokens(str(leaf).replace("_", " "))
    if spaced:
        return spaced
    raw = re.sub(r"[^a-z0-9]+", "", str(leaf).casefold())
    return {raw} if raw else set()


def _key_phrases(leaf: str) -> list[str]:
    raw = str(leaf).casefold()
    spaced = raw.replace("_", " ").strip()
    out: list[str] = []
    for phrase in (raw, spaced):
        if phrase and phrase not in out and phrase not in STOPWORDS:
            out.append(phrase)
    return sorted(out, key=len, reverse=True)


def _flatten_leaves(obj: Any, prefix: str = "") -> dict[str, Any]:
    leaves: dict[str, Any] = {}
    if isinstance(obj, dict):
        for key, val in obj.items():
            leaf = str(key)
            if leaf in _SKIP_LEAF_KEYS:
                continue
            path = f"{prefix}.{leaf}" if prefix else leaf
            leaves.update(_flatten_leaves(val, path))
        return leaves
    if isinstance(obj, list):
        for i, val in enumerate(obj):
            path = f"{prefix}.{i}" if prefix else str(i)
            leaves.update(_flatten_leaves(val, path))
        return leaves
    if prefix:
        leaves[prefix] = obj
    return leaves


def _value_blob(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


def _value_tokens(value: Any) -> set[str]:
    return content_tokens(_value_blob(value))


def _value_nums(value: Any) -> set[str]:
    return {_norm(x) for x in _NUM_RE.findall(_value_blob(value))}


def _payload_token_set(leaves: dict[str, Any]) -> set[str]:
    toks: set[str] = set()
    for path, value in leaves.items():
        toks |= _key_tokens(_leaf_key(path))
        toks |= _value_tokens(value)
    return toks


def _resolve_field(name: str, leaves: dict[str, Any]) -> list[str]:
    ntoks = _key_tokens(name)
    if not ntoks:
        return []
    exact: list[str] = []
    partial: list[str] = []
    for path in leaves:
        ktoks = _key_tokens(_leaf_key(path))
        if not ktoks:
            continue
        if ntoks == ktoks:
            exact.append(path)
        elif ntoks <= ktoks or ktoks <= ntoks:
            partial.append(path)
    return exact or partial


def _copula_mismatches(text: str, leaves: dict[str, Any]) -> set[str]:
    missing: set[str] = set()
    for match in _COPULA_RE.finditer(text):
        if match.group("neg"):
            missing.add("negation")
            continue
        field = str(match.group("field") or "").strip()
        value = str(match.group("value") or "").strip()
        vtoks = content_tokens(value)
        paths = _resolve_field(field, leaves)
        if not paths:
            continue
        if not vtoks:
            missing.add(f"field_mismatch:{_leaf_key(paths[0])}")
            continue
        if not any(vtoks <= _value_tokens(leaves[path]) for path in paths):
            missing.add(f"field_mismatch:{_leaf_key(paths[0])}")
    return missing


def _field_number_mismatches(text: str, leaves: dict[str, Any]) -> set[str]:
    folded = str(text or "").casefold()
    missing: set[str] = set()
    for path, value in leaves.items():
        leaf = _leaf_key(path)
        if leaf.isdigit():
            continue
        field_nums = _value_nums(value)
        for phrase in _key_phrases(leaf):
            pat = re.compile(
                rf"(?<![\w]){re.escape(phrase)}(?![\w])\s+(?:score\s+)?(?:of\s+|is\s+|:\s*)?({_NUM_PAT})",
                re.UNICODE,
            )
            for hit in pat.finditer(folded):
                num = _norm(hit.group(1))
                if num not in field_nums:
                    missing.add(f"field_mismatch:{leaf}")
    return missing


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
    """Claim tokens/numbers that are not field-true in the cited factual payload."""
    text = str(claim_text or "").strip()
    eid = str(evidence_id or "").strip()
    if not text or not eid:
        return {"empty_claim_or_evidence_id"}
    item = find_evidence_item(evidence, eid)
    if item is None:
        return {"evidence_item_missing"}
    leaves = _flatten_leaves(factual_payload(item))
    missing: set[str] = set()
    ev_nums = set()
    for value in leaves.values():
        ev_nums |= _value_nums(value)
    for m in _NUM_RE.findall(text):
        if _norm(m) not in ev_nums:
            missing.add(str(m))
    ctoks = content_tokens(text)
    if not ctoks:
        missing.add("no_content_tokens")
        return missing
    missing |= ctoks - _payload_token_set(leaves)
    missing |= _copula_mismatches(text, leaves)
    missing |= _field_number_mismatches(text, leaves)
    return missing


def claim_is_supported(
    claim_text: str,
    evidence_id: str,
    evidence: list[Any] | None,
) -> bool:
    """True only if claim tokens exist in payload and field/value pairings match."""
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
