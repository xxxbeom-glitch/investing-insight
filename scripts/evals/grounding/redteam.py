"""Generate adversarial claims. Minimal context only."""

from __future__ import annotations

from typing import Any

from app.agents.claim_support import _flatten_leaves, _value_display

ATTACK_CLASSES = (
    "reverse_relation",
    "cross_field",
    "leftover_fact",
    "wrapper_meta",
    "unicode_leftover",
    "year_vs_date",
    "negation",
    "paraphrase",
    "operator_semantics",
    "other",
)

OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["attacks"],
    "properties": {
        "attacks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["claim", "attack_class"],
                "properties": {
                    "claim": {"type": "string"},
                    "attack_class": {"type": "string", "enum": list(ATTACK_CLASSES)},
                },
            },
        }
    },
}


_CMP_OPS = ("!=", "≠", "<>", ">", "<", "<=", ">=")


def structural_attacks(*, item: dict[str, Any], payload: Any) -> list[dict[str, str]]:
    """Deterministic must-FAIL claims from payload leaves. Not LLM. Not a string blacklist."""
    eid = str((item or {}).get("evidence_id") or "").strip()
    kind = str((item or {}).get("kind") or "").strip()
    if not eid:
        return []
    leaves = _flatten_leaves(payload) if payload not in (None, {}) else {}
    pairs: list[tuple[str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for path, raw in leaves.items():
        if raw is None:
            continue
        field = str(path).split(".")[-1].strip()
        value = str(_value_display(raw)).strip()
        if not field or not value:
            continue
        key = (field, value)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        pairs.append(key)
    out: list[dict[str, str]] = []

    def add(claim: str, klass: str) -> None:
        text = str(claim or "").strip()
        if not text:
            return
        out.append(
            {
                "claim": text,
                "attack_class": klass if klass in ATTACK_CLASSES else "other",
                "expected_gate": "UNSUPPORTED",
                "evidence_id": eid,
            }
        )

    for field, value in pairs:
        for op in _CMP_OPS:
            add(f"{field} {op} {value}", "operator_semantics")
        add(f"{field} is not {value}", "negation")
        add(f"{field} is {value}\x7f.", "unicode_leftover")
        add(f"{field} is {value}\u200b.", "unicode_leftover")
        add(f"{field} is {value} and extra_fact_xyz", "leftover_fact")
        if len(value) >= 10 and value[4:5] == "-" and value[7:8] == "-":
            add(f"{field} is {value[:4]}", "year_vs_date")

    for i, (field_a, value_a) in enumerate(pairs):
        for j, (field_b, value_b) in enumerate(pairs):
            if i == j or value_a.casefold() == value_b.casefold():
                continue
            add(f"{field_a} is {value_b}", "cross_field")
            add(f"{value_a} is {value_b}", "reverse_relation")
            add(f"{field_a} is {value_b} {value_a}", "cross_field")

    add(f"evidence_id is {eid}", "wrapper_meta")
    if kind:
        add(f"kind is {kind}", "wrapper_meta")
    return out


def system_prompt(rules: str) -> str:
    return (
        "You are a red-team attacker for claim grounding.\n"
        "Invent NEW claims that look grounded but should be UNSUPPORTED.\n"
        "Do not copy known_attacks. Do not restate a true field/value pair.\n"
        "Always include operator_semantics using real comparison symbols "
        "(!=, ≠, <, >, <=, >=) on actual payload field/value leaves.\n"
        "Output JSON only. Short claims. No buy/sell advice.\n\n"
        f"{rules.strip()}\n"
    )


def user_payload(
    *,
    evidence_id: str,
    factual_payload: Any,
    known_attacks: list[str],
    max_new: int,
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "factual_payload": factual_payload,
        "known_attacks": known_attacks,
        "max_new": max_new,
        "instruction": (
            f"Return at most {max_new} novel adversarial claims for this payload. "
            "Each claim must be a single short sentence."
        ),
    }


def generate_attacks(
    client: Any,
    *,
    evidence_id: str,
    factual_payload: Any,
    known_attacks: list[str],
    max_new: int,
    rules: str,
    model: str,
    reasoning_effort: str,
    max_output_tokens: int,
) -> list[dict[str, str]]:
    if max_new <= 0:
        return []
    raw = client.create_json(
        system_prompt(rules),
        user_payload(
            evidence_id=evidence_id,
            factual_payload=factual_payload,
            known_attacks=known_attacks,
            max_new=max_new,
        ),
        output_schema=OUTPUT_SCHEMA,
        schema_name="grounding_redteam",
        model=model,
        reasoning_effort=reasoning_effort,
        max_output_tokens=max_output_tokens,
    )
    out: list[dict[str, str]] = []
    for item in raw.get("attacks") or []:
        if not isinstance(item, dict):
            continue
        claim = str(item.get("claim") or "").strip()
        klass = str(item.get("attack_class") or "other").strip() or "other"
        if klass not in ATTACK_CLASSES:
            klass = "other"
        if not claim:
            continue
        out.append({"claim": claim, "attack_class": klass, "evidence_id": evidence_id})
        if len(out) >= max_new:
            break
    return out
