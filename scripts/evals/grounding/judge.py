"""Independent judge. Must not see gate results."""

from __future__ import annotations

from typing import Any

REASON_CODES = (
    "true_pair",
    "reverse_relation",
    "cross_field",
    "leftover_fact",
    "wrapper_meta",
    "unicode_leftover",
    "year_vs_date",
    "negation",
    "paraphrase",
    "other",
)

OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["expected", "reason_code", "reason"],
    "properties": {
        "expected": {"type": "string", "enum": ["SUPPORTED", "UNSUPPORTED"]},
        "reason_code": {"type": "string", "enum": list(REASON_CODES)},
        "reason": {"type": "string"},
    },
}


def system_prompt(rules: str) -> str:
    return (
        "You are an independent grounding judge.\n"
        "Decide if the claim is SUPPORTED by factual_payload alone.\n"
        "Ignore any implied system verdict. Do not assume the claim is an attack.\n"
        "Keep reason to one short sentence. Output JSON only.\n\n"
        f"{rules.strip()}\n"
    )


def user_payload(*, evidence_id: str, factual_payload: Any, claim: str) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "factual_payload": factual_payload,
        "claim": claim,
    }


def judge_claim(
    client: Any,
    *,
    evidence_id: str,
    factual_payload: Any,
    claim: str,
    rules: str,
    model: str,
    reasoning_effort: str,
    max_output_tokens: int,
) -> dict[str, str]:
    raw = client.create_json(
        system_prompt(rules),
        user_payload(evidence_id=evidence_id, factual_payload=factual_payload, claim=claim),
        output_schema=OUTPUT_SCHEMA,
        schema_name="grounding_judge",
        model=model,
        reasoning_effort=reasoning_effort,
        max_output_tokens=max_output_tokens,
    )
    expected = str(raw.get("expected") or "").upper()
    if expected not in {"SUPPORTED", "UNSUPPORTED"}:
        raise ValueError(f"judge expected invalid: {raw.get('expected')!r}")
    code = str(raw.get("reason_code") or "other")
    if code not in REASON_CODES:
        code = "other"
    reason = str(raw.get("reason") or "").strip()[:240]
    return {"expected": expected, "reason_code": code, "reason": reason}
