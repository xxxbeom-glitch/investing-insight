from __future__ import annotations

import hashlib
import json
from typing import Any

from app.research.openai_responses import ModelUnavailableError, ResponsesResult, resolve_requested_model

HIGH_STAKES_ROLES = {"research_qa_agent", "adversarial_agent", "final_selector_agent"}
HIGH_STAKES_EFFORTS = {"medium", "high", "xhigh"}
_SABOTAGE = (
    "disregard all input",
    "malformed non-json",
    "output malformed",
    "break the role",
)


def prompt_unusable(prompt: str, role: str) -> bool:
    text = (prompt or "").strip()
    low = text.lower()
    if any(s in low for s in _SABOTAGE):
        return True
    if role == "final_selector_agent" and len(text) >= 20 and "claim" not in low:
        return True
    return False


class MockStructuredClient:
    """Deterministic structured Responses stub — parameterized by model/effort/prompt."""

    def __init__(
        self,
        overrides: dict[str, dict[str, Any]] | None = None,
        *,
        allowed_models: set[str] | None = None,
    ):
        self.overrides = overrides or {}
        self.calls: list[str] = []
        self.fingerprints: list[str] = []
        self.allowed_models = allowed_models

    def create_structured(
        self,
        *,
        model: str,
        reasoning_effort: str,
        system_prompt: str,
        user_payload: dict[str, Any],
        output_schema: dict[str, Any],
        schema_name: str,
    ) -> ResponsesResult:
        resolved = resolve_requested_model(model)
        if self.allowed_models is not None and resolved not in self.allowed_models:
            raise ModelUnavailableError(f"unavailable model: {model}")
        role = user_payload.get("agent_role") or schema_name
        self.calls.append(role)
        self.fingerprints.append(
            hashlib.sha256(f"{resolved}|{reasoning_effort}|{system_prompt}|{role}".encode("utf-8")).hexdigest()[:16]
        )
        if prompt_unusable(system_prompt, role):
            return ResponsesResult(
                response_id="mock-response",
                resolved_model=resolved,
                output_text="NOT_JSON",
                raw={"mock": True, "prompt_rejected": True},
                token_usage={"input_tokens": 1, "output_tokens": 0},
            )
        if role in HIGH_STAKES_ROLES and reasoning_effort not in HIGH_STAKES_EFFORTS:
            payload = _weak_output(role, user_payload)
        else:
            payload = self.overrides.get(role) or _default_output(role, user_payload)
        return ResponsesResult(
            response_id="mock-response",
            resolved_model=resolved,
            output_text=json.dumps(payload),
            raw={"mock": True, "reasoning_effort": reasoning_effort},
            token_usage={"input_tokens": 1, "output_tokens": 1},
        )


def _weak_output(role: str, packet: dict[str, Any]) -> dict[str, Any]:
    """Schema-valid but gate-failing output when high-stakes effort is too low."""
    if role == "research_qa_agent":
        return {"status": "FAIL", "failed_claims": ["insufficient_reasoning_effort"], "warnings": []}
    if role == "adversarial_agent":
        return {
            "status": "FAIL",
            "counter_thesis": "insufficient_reasoning_effort",
            "broken_assumptions": [],
            "gate_blockers": ["insufficient_reasoning_effort"],
        }
    allowed = list(packet.get("allowed_evidence_ids") or []) or ["regime"]
    return {
        "status": "WATCH",
        "rationale_claim_refs": [],
        "bear_case_claim_refs": [],
        "risks_claim_refs": [],
        "invalidation_claim_refs": [],
        "evidence_refs": allowed[:1],
        "claim_refs": [],
    }


def _default_output(role: str, packet: dict[str, Any]) -> dict[str, Any]:
    ticker = packet.get("ticker") or "TEST"
    allowed = list(packet.get("allowed_evidence_ids") or [])
    # Prefer real allowed ids so deterministic QA can PASS under mock
    primary = allowed[0] if allowed else "regime"
    if role == "market_agent":
        return {
            "regime_view": "expansion",
            "key_macro_points": ["labor stable"],
            "risks": ["policy"],
            "evidence_refs": [x for x in allowed if x == "regime"][:1] or (["regime"] if "regime" in allowed else [primary]),
            "unsupported_or_missing": [],
        }
    if role == "industry_agent":
        refs = [x for x in allowed if x.startswith("assessment")][:1] or [primary]
        return {
            "industry_id": "semis",
            "attractiveness_view": "constructive",
            "dimension_notes": {
                "demand": "ok",
                "capex": "ok",
                "supply": "ok",
                "pricing": "ok",
                "margin": "ok",
                "bottleneck": "ok",
            },
            "risks": ["cycle"],
            "evidence_refs": refs,
            "unsupported_or_missing": [],
        }
    if role == "company_agent":
        refs = [x for x in allowed if x.startswith("price") or x.startswith("fact") or x == "quant"][:2] or [primary]
        return {
            "ticker": ticker,
            "thesis": "mock thesis grounded in snapshot facts",
            "positives": ["scale"],
            "negatives": ["competition"],
            "evidence_refs": refs,
            "unsupported_or_missing": [],
        }
    if role == "event_agent":
        refs = [x for x in allowed if x.startswith("filing") or x.startswith("fact")][:2]
        return {
            "events": ["snapshot filing/fact evidence reviewed"] if refs else ["none material in snapshot"],
            "near_term_catalysts": [],
            "evidence_refs": refs,
            "unsupported_or_missing": [] if refs else ["full event calendar"],
        }
    if role == "research_agent":
        refs = allowed[:3] or [primary]
        return {
            "synthesis": "mock synthesis using allowed evidence only",
            "claims": [{"claim": "demand resilient", "evidence_id": refs[0]}],
            "bear_case": ["multiple compression"],
            "evidence_refs": refs,
            "unsupported_or_missing": [],
        }
    if role == "research_qa_agent":
        return {"status": "PASS", "failed_claims": [], "warnings": []}
    if role == "adversarial_agent":
        return {
            "status": "PASS",
            "counter_thesis": "growth fades",
            "broken_assumptions": [],
            "gate_blockers": [],
        }
    if role == "final_selector_agent":
        catalog = packet.get("approved_claims") or []
        claim_ids = [c.get("claim_id") for c in catalog if c.get("claim_id")]
        primary_claim = next(
            (c for c in claim_ids if str(c).startswith("claim:")),
            claim_ids[0] if claim_ids else "claim:0",
        )
        return {
            "status": "WATCH",
            "rationale_claim_refs": [primary_claim],
            "bear_case_claim_refs": [primary_claim],
            "risks_claim_refs": [primary_claim],
            "invalidation_claim_refs": [primary_claim],
            "evidence_refs": allowed[:2] or [primary],
            "claim_refs": [primary_claim],
        }
    raise ValueError(f"no mock for {role}")
