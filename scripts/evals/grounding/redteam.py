"""Generate adversarial claims. Minimal context only."""

from __future__ import annotations

from typing import Any

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


def system_prompt(rules: str) -> str:
    return (
        "You are a red-team attacker for claim grounding.\n"
        "Invent NEW claims that look grounded but should be UNSUPPORTED.\n"
        "Do not copy known_attacks. Do not restate a true field/value pair.\n"
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
