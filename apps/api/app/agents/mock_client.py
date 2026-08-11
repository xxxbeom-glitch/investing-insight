from __future__ import annotations

import json
from typing import Any

from app.research.openai_responses import ModelUnavailableError, ResponsesResult


class MockStructuredClient:
    """Deterministic structured Responses stub — no network, no free-chat."""

    def __init__(
        self,
        overrides: dict[str, dict[str, Any]] | None = None,
        *,
        allowed_models: set[str] | None = None,
    ):
        self.overrides = overrides or {}
        self.calls: list[str] = []
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
        if self.allowed_models is not None and model not in self.allowed_models:
            raise ModelUnavailableError(f"unavailable model: {model}")
        role = user_payload.get("agent_role") or schema_name
        self.calls.append(role)
        payload = self.overrides.get(role) or _default_output(role, user_payload)
        return ResponsesResult(
            response_id="mock-response",
            resolved_model=model,
            output_text=json.dumps(payload),
            raw={"mock": True},
            token_usage={"input_tokens": 1, "output_tokens": 1},
        )


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
            "evidence_refs": [x for x in allowed if x == "regime"][:1] or ["regime"],
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
        primary_claim = next((c for c in claim_ids if str(c).startswith("claim:")), claim_ids[0] if claim_ids else "claim:0")
        bear_id = next((c for c in claim_ids if "bear" in str(c) or str(c).startswith("adv:")), primary_claim)
        return {
            "status": "WATCH",
            "rationale_claim_refs": [primary_claim],
            "bear_case_claim_refs": [bear_id],
            "risks_claim_refs": [bear_id],
            "invalidation_claim_refs": [primary_claim],
            "evidence_refs": allowed[:2] or [primary],
            "claim_refs": [primary_claim, bear_id],
        }
    raise ValueError(f"no mock for {role}")
