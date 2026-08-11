"""FP/FN matrix. positive = gate SUPPORTED. No LLM."""

from __future__ import annotations

from typing import Any

SUPPORTED = "SUPPORTED"
UNSUPPORTED = "UNSUPPORTED"


def normalize_claim(text: str) -> str:
    return " ".join(str(text or "").casefold().split())


def claim_key(text: str, evidence_id: str) -> tuple[str, str]:
    return (str(evidence_id or "").strip(), normalize_claim(text))


def gate_label(supported: bool) -> str:
    return SUPPORTED if supported else UNSUPPORTED


def classify(*, judge_expected: str | None, gate_actual: str) -> str:
    """Return FP | FN | TP | TN | BLOCKED.

    BLOCKED = gate UNSUPPORTED and judge not called (cost skip).
    Counted as TN in totals.
    """
    gate = str(gate_actual or "").upper()
    if judge_expected is None:
        if gate == UNSUPPORTED:
            return "TN"
        return "UNGRADED"
    expected = str(judge_expected).upper()
    if expected == UNSUPPORTED and gate == SUPPORTED:
        return "FP"
    if expected == SUPPORTED and gate == UNSUPPORTED:
        return "FN"
    if expected == SUPPORTED and gate == SUPPORTED:
        return "TP"
    if expected == UNSUPPORTED and gate == UNSUPPORTED:
        return "TN"
    return "UNGRADED"


def tally(rows: list[dict[str, Any]]) -> dict[str, int]:
    out = {"FP": 0, "FN": 0, "TP": 0, "TN": 0, "UNGRADED": 0}
    for row in rows:
        label = str(row.get("matrix") or "UNGRADED")
        if label not in out:
            label = "UNGRADED"
        out[label] += 1
    return out
