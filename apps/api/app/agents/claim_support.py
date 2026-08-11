"""Deterministic claim↔evidence support via field/operator/value triples.

Allowed evidence_id is not proof of support. Token-bag subset is not sufficient.
Copula words are stopwords, not a regex ladder.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from app.research.numeric_scale import (
    _NUM_RE,
    _norm,
    iter_quantities,
    phrase_matches_absolute,
    quantity_matches_absolute,
    to_decimal,
)

# Closed-class function words only. Not a fact denylist. Not a copula matcher.
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
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
_DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_COPULA_AFTER = re.compile(r"^\s*(?:is|was|were|are)(?![\w])\s*|^\s*:\s*")
_COPULA_BEFORE = re.compile(r"(?:(?<![A-Za-z])(?:is|was|were|are)|:)\s*$")
_SCAFFOLD_TOKEN = re.compile(r"\s*([^\W\d_]+)", re.UNICODE)
# Keep ordinary whitespace; reject other Cc and all Cf (ZWSP, DEL, BOM, …).
_ALLOWED_CC = frozenset("\t\n\r")


@dataclass(frozen=True)
class ClaimTriple:
    """Verification triple. `operator` is always `equals`; other relations fail closed."""

    field: str
    operator: str
    value: str


@dataclass(frozen=True)
class _Leaf:
    path: str
    field: str
    phrases: tuple[str, ...]
    value_raw: Any
    value_folded: str
    numeric_norm: str | None
    date_phrase: str | None


@dataclass(frozen=True)
class _Span:
    start: int
    end: int
    kind: str  # "field" | "value"
    paths: tuple[str, ...]
    phrase: str


def claim_text_hash(text: str, evidence_id: str) -> str:
    norm = " ".join(str(text or "").split())
    blob = f"{evidence_id}\n{norm}".encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


_ASCII_CMP_OP = re.compile(r"!==|!=|<>|<=|>=")


def _is_unsupported_relation_char(ch: str) -> bool:
    if ch in "=＝":
        return False
    if ch in "<>≠≤≥≮≯≰≱≢":
        return True
    name = unicodedata.name(ch, "")
    if not name or name in {"EQUALS SIGN", "FULLWIDTH EQUALS SIGN"}:
        return False
    return any(
        marker in name
        for marker in (
            "LESS-THAN",
            "GREATER-THAN",
            "NOT EQUAL",
            "NOT-EQUAL",
            "NOT IDENTICAL",
        )
    )


def _has_unsupported_operator(text: str) -> bool:
    """Only equality is supported. Comparison/inequality symbols fail closed."""
    if _ASCII_CMP_OP.search(text):
        return True
    return any(_is_unsupported_relation_char(ch) for ch in text)


def _has_disallowed_control_or_format(text: str) -> bool:
    for ch in text:
        cat = unicodedata.category(ch)
        if cat == "Cf":
            return True
        if cat == "Cc" and ch not in _ALLOWED_CC:
            return True
    return False


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
        if phrase and phrase not in out:
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


def _numeric_norm(value: Any) -> str | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return _norm(value)
    text = str(value).strip()
    if not text or _DATE_ONLY_RE.match(text):
        return None
    try:
        return _norm(float(text))
    except (TypeError, ValueError):
        return None


def _date_phrase(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    match = _DATE_RE.match(text)
    return match.group(0) if match else None


def _value_display(value: Any) -> str:
    if isinstance(value, bool) or value is None:
        return str(value).casefold()
    return str(value)


def _inventory(leaves: dict[str, Any]) -> dict[str, _Leaf]:
    out: dict[str, _Leaf] = {}
    for path, raw in leaves.items():
        if raw is None:
            continue
        field = _leaf_key(path)
        folded = " ".join(_value_display(raw).casefold().split())
        out[path] = _Leaf(
            path=path,
            field=field,
            phrases=tuple(_key_phrases(field)),
            value_raw=raw,
            value_folded=folded,
            numeric_norm=_numeric_norm(raw),
            date_phrase=_date_phrase(raw),
        )
    return out


def _find_phrase_spans(folded: str, phrase: str) -> list[tuple[int, int]]:
    if not phrase:
        return []
    spans: list[tuple[int, int]] = []
    if re.search(r"[0-9a-z]", phrase, re.I):
        for match in re.finditer(rf"(?<![\w]){re.escape(phrase)}(?![\w])", folded):
            spans.append((match.start(), match.end()))
        return spans
    start = 0
    while True:
        idx = folded.find(phrase, start)
        if idx < 0:
            break
        spans.append((idx, idx + len(phrase)))
        start = idx + max(len(phrase), 1)
    return spans


def _value_phrases(leaf: _Leaf) -> list[str]:
    phrases: list[str] = []
    if leaf.date_phrase:
        phrases.append(leaf.date_phrase)
    if leaf.numeric_norm is None and leaf.value_folded:
        phrases.append(leaf.value_folded)
    out: list[str] = []
    for phrase in phrases:
        if phrase and phrase not in out:
            out.append(phrase)
    return out


def _collect_candidates(folded: str, inv: dict[str, _Leaf]) -> list[_Span]:
    grouped: dict[tuple[int, int, str, str], set[str]] = {}

    def add(start: int, end: int, kind: str, path: str, phrase: str) -> None:
        key = (start, end, kind, phrase)
        grouped.setdefault(key, set()).add(path)

    for leaf in inv.values():
        for phrase in leaf.phrases:
            for start, end in _find_phrase_spans(folded, phrase):
                add(start, end, "field", leaf.path, phrase)
        for phrase in _value_phrases(leaf):
            for start, end in _find_phrase_spans(folded, phrase):
                add(start, end, "value", leaf.path, phrase)
        if leaf.numeric_norm is not None:
            mag = to_decimal(leaf.value_raw)
            if mag is not None:
                for qty in iter_quantities(folded):
                    if quantity_matches_absolute(mag, qty):
                        add(qty.start, qty.end, "value", leaf.path, folded[qty.start : qty.end])
            for match in _NUM_RE.finditer(folded):
                # `81.32A` is not 81.32. _NUM_RE only blocks a leading letter.
                nxt = folded[match.end() : match.end() + 1]
                if nxt.isalpha():
                    continue
                if _norm(match.group(0)) == leaf.numeric_norm:
                    add(match.start(), match.end(), "value", leaf.path, match.group(0))
    return [
        _Span(start=start, end=end, kind=kind, paths=tuple(sorted(paths)), phrase=phrase)
        for (start, end, kind, phrase), paths in grouped.items()
    ]


def _pick_spans(candidates: list[_Span]) -> list[_Span]:
    chosen: list[_Span] = []
    occupied: list[tuple[int, int]] = []

    def overlaps(start: int, end: int) -> bool:
        for a, b in occupied:
            if start < b and end > a:
                return True
        return False

    for span in sorted(candidates, key=lambda s: (-(s.end - s.start), s.start, s.kind)):
        if span.end <= span.start:
            continue
        if overlaps(span.start, span.end):
            continue
        chosen.append(span)
        occupied.append((span.start, span.end))
    return sorted(chosen, key=lambda s: s.start)


def _leaf_value_mentioned(leaf: _Leaf, value_spans: list[_Span], inv: dict[str, _Leaf]) -> bool:
    for span in value_spans:
        if leaf.path not in span.paths:
            continue
        # Numeric: span must be this leaf's number, not a sibling that shares a path set.
        if leaf.numeric_norm is not None:
            if _norm(span.phrase) == leaf.numeric_norm:
                return True
            if phrase_matches_absolute(span.phrase, leaf.value_raw):
                return True
            continue
        if leaf.date_phrase and span.phrase == leaf.date_phrase:
            return True
        if span.phrase == leaf.value_folded:
            return True
        other = inv.get(span.paths[0]) if span.paths else None
        if other is not None and other.path == leaf.path:
            return True
    return False


def _field_vocab(inv: dict[str, _Leaf]) -> set[str]:
    toks: set[str] = set()
    for leaf in inv.values():
        toks |= _key_tokens(leaf.field)
        for part in leaf.path.replace("_", ".").split("."):
            toks |= _key_tokens(part)
    return toks


def _span_gap(a: _Span, b: _Span) -> int | None:
    if a.end <= b.start:
        return b.start - a.end
    if b.end <= a.start:
        return a.start - b.end
    return None


def _skip_field_scaffold(text: str, vocab: set[str]) -> tuple[str, int]:
    """Skip cited field-name scaffolding (`score` in `demand score is 81.32`). Do not skip copulas."""
    pos = 0
    while True:
        m = _SCAFFOLD_TOKEN.match(text[pos:])
        if not m:
            break
        tok = m.group(1)
        if tok in {"is", "was", "were", "are"} or tok not in vocab:
            break
        pos += m.end()
    return text[pos:], pos


def _has_value_value_copula(
    folded: str,
    value_spans: list[_Span],
    field_spans: list[_Span],
) -> bool:
    """Value copula value pairs two leaves without a field. Equality contract forbids that."""
    for left in value_spans:
        matched = _COPULA_AFTER.match(folded[left.end :])
        if not matched:
            continue
        obj_at = left.end + matched.end()
        later = [v for v in value_spans if v.start >= obj_at]
        if not later:
            continue
        nearest = min(later, key=lambda v: (v.start, v.end))
        if any(obj_at <= fs.start and fs.end <= nearest.start for fs in field_spans):
            continue
        return True
    return False


def _copula_directed_value(
    field_span: _Span,
    folded: str,
    value_spans: list[_Span],
    vocab: set[str],
) -> tuple[bool, _Span | None]:
    """If a copula attaches to this field, return that object only (no farther rescue)."""
    after_raw = folded[field_span.end :]
    after, skipped = _skip_field_scaffold(after_raw, vocab)
    matched = _COPULA_AFTER.match(after)
    if matched:
        obj_at = field_span.end + skipped + matched.end()
        later = [v for v in value_spans if v.start >= obj_at]
        return True, min(later, key=lambda v: (v.start, v.end)) if later else None
    before = folded[: field_span.start]
    matched_b = _COPULA_BEFORE.search(before)
    if matched_b:
        earlier = [v for v in value_spans if v.end <= matched_b.start()]
        return True, max(earlier, key=lambda v: (v.end, v.start)) if earlier else None
    return False, None


def _bind_value_span(
    field_span: _Span,
    folded: str,
    value_spans: list[_Span],
    inv: dict[str, _Leaf],
) -> _Span | None:
    found, copula_value = _copula_directed_value(field_span, folded, value_spans, _field_vocab(inv))
    if found:
        return copula_value
    return _nearest_value_span(field_span, value_spans, inv)


def _nearest_value_span(
    field_span: _Span,
    value_spans: list[_Span],
    inv: dict[str, _Leaf],
) -> _Span | None:
    """Closest value. Equal gaps: prefer a value owned by this field, not a farther rescue."""
    scored: list[tuple[int, int, int, _Span]] = []
    for value in value_spans:
        gap = _span_gap(field_span, value)
        if gap is None:
            continue
        owned = any(
            path in value.paths
            and path in inv
            and path in field_span.paths
            and _leaf_value_mentioned(inv[path], [value], inv)
            for path in field_span.paths
        )
        scored.append((gap, 0 if owned else 1, value.start, value))
    if not scored:
        return None
    scored.sort()
    min_gap = scored[0][0]
    group = [row for row in scored if row[0] == min_gap]
    group.sort()
    return group[0][3]


def _leftover_tokens(folded: str, spans: list[_Span], inv: dict[str, _Leaf]) -> set[str]:
    chars = list(folded)
    for span in spans:
        for i in range(span.start, min(span.end, len(chars))):
            chars[i] = " "
    remain = "".join(chars)
    leftover = content_tokens(remain)
    leftover -= _field_vocab(inv)
    leftover -= STOPWORDS
    return leftover


def parse_claim_against_leaves(text: str, leaves: dict[str, Any]) -> tuple[list[ClaimTriple], set[str]]:
    """Recover field/operator/value triples from claim text × payload inventory."""
    raw = str(text or "")
    if _has_disallowed_control_or_format(raw):
        return [], {"disallowed_control_or_format"}
    if _has_unsupported_operator(raw):
        return [], {"unsupported_operator"}
    raw = raw.strip()
    if not raw:
        return [], {"empty_claim_or_evidence_id"}
    inv = _inventory(leaves)
    folded = raw.casefold()
    ctoks = content_tokens(raw)
    if not ctoks:
        return [], {"no_content_tokens"}
    if not inv:
        return [], ctoks or {"empty_inventory"}

    spans = _pick_spans(_collect_candidates(folded, inv))
    field_spans = [s for s in spans if s.kind == "field"]
    value_spans = [s for s in spans if s.kind == "value"]
    if _has_value_value_copula(folded, value_spans, field_spans):
        return [], {"value_value_copula"}
    missing: set[str] = set()
    missing |= _leftover_tokens(folded, spans, inv)

    triples: list[ClaimTriple] = []
    bound: set[str] = set()
    used_values: set[tuple[int, int, str]] = set()

    mentioned_paths = {path for fs in field_spans for path in fs.paths}

    for field_span in field_spans:
        nearest = _bind_value_span(field_span, folded, value_spans, inv)
        label = field_span.phrase.replace(" ", "_") or "field"
        if nearest is None:
            missing.add(f"field_mismatch:{label}")
            continue
        matching = [
            inv[path]
            for path in field_span.paths
            if path in inv and _leaf_value_mentioned(inv[path], [nearest], inv)
        ]
        value_key = (nearest.start, nearest.end, nearest.phrase)
        if len(matching) != 1:
            missing.add(f"field_mismatch:{label}")
            continue
        leaf = matching[0]
        if value_key in used_values and leaf.path not in bound:
            missing.add(f"field_mismatch:{label}")
            continue
        bound.add(leaf.path)
        used_values.add(value_key)
        triples.append(ClaimTriple(field=leaf.field, operator="equals", value=_value_display(leaf.value_raw)))

    for span in value_spans:
        value_key = (span.start, span.end, span.phrase)
        if value_key in used_values:
            continue
        owners = [inv[p] for p in span.paths if p in inv]
        if any(leaf.path in bound for leaf in owners):
            continue
        if any(leaf.path in mentioned_paths for leaf in owners):
            continue
        exact = [leaf for leaf in owners if _leaf_value_mentioned(leaf, [span], inv)]
        if len(exact) == 1:
            leaf = exact[0]
            bound.add(leaf.path)
            used_values.add(value_key)
            triples.append(ClaimTriple(field=leaf.field, operator="equals", value=_value_display(leaf.value_raw)))
        elif len(exact) > 1:
            missing.add(f"ambiguous_value:{span.phrase}")
        else:
            missing.add(f"field_mismatch:{span.phrase}")

    if not bound:
        missing.add("no_field_binding")

    # Stable unique triples
    uniq: list[ClaimTriple] = []
    seen: set[tuple[str, str, str]] = set()
    for triple in triples:
        key = (triple.field, triple.operator, triple.value)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(triple)
    return uniq, missing


def find_evidence_item(
    evidence: list[Any] | None,
    evidence_id: str,
) -> dict[str, Any] | None:
    eid = str(evidence_id or "").strip()
    for item in evidence or []:
        if isinstance(item, dict) and str(item.get("evidence_id") or "").strip() == eid:
            return item
    return None


def parse_claim(
    claim_text: str,
    evidence_id: str,
    evidence: list[Any] | None,
) -> tuple[list[ClaimTriple], set[str]]:
    raw = str(claim_text or "")
    if _has_disallowed_control_or_format(raw):
        return [], {"disallowed_control_or_format"}
    if _has_unsupported_operator(raw):
        return [], {"unsupported_operator"}
    text = raw.strip()
    eid = str(evidence_id or "").strip()
    if not text or not eid:
        return [], {"empty_claim_or_evidence_id"}
    item = find_evidence_item(evidence, eid)
    if item is None:
        return [], {"evidence_item_missing"}
    leaves = _flatten_leaves(factual_payload(item))
    return parse_claim_against_leaves(text, leaves)


def claim_unsupported_tokens(
    claim_text: str,
    evidence_id: str,
    evidence: list[Any] | None,
) -> set[str]:
    """Unsupported unless recovered triples match cited leaves and no leftover facts remain."""
    _triples, missing = parse_claim(claim_text, evidence_id, evidence)
    return missing


def claim_is_supported(
    claim_text: str,
    evidence_id: str,
    evidence: list[Any] | None,
) -> bool:
    """True only if structured field/equals/value triples match the cited payload."""
    triples, missing = parse_claim(claim_text, evidence_id, evidence)
    return bool(triples) and not missing


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
