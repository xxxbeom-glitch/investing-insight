from __future__ import annotations

import json
from typing import Any

from app.research.openai_responses import ResponsesResult


class MockStructuredClient:
    """Deterministic structured Responses stub — no network, no free-chat."""

    def __init__(self, overrides: dict[str, dict[str, Any]] | None = None):
        self.overrides = overrides or {}
        self.calls: list[str] = []

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
    if role == "market_agent":
        return {
            "regime_view": "expansion",
            "key_macro_points": ["labor stable"],
            "risks": ["policy"],
            "evidence_refs": ["regime"],
            "unsupported_or_missing": [],
        }
    if role == "industry_agent":
        return {
            "industry_id": "semis",
            "attractiveness_view": "constructive",
            "dimension_notes": {"demand": "ok"},
            "risks": ["cycle"],
            "evidence_refs": ["assessment:semis"],
            "unsupported_or_missing": [],
        }
    if role == "company_agent":
        return {
            "ticker": ticker,
            "thesis": "mock thesis",
            "positives": ["scale"],
            "negatives": ["competition"],
            "evidence_refs": ["union"],
            "unsupported_or_missing": [],
        }
    if role == "event_agent":
        return {
            "events": ["none material in snapshot"],
            "near_term_catalysts": [],
            "evidence_refs": [],
            "unsupported_or_missing": ["full event calendar"],
        }
    if role == "research_agent":
        return {
            "synthesis": "mock synthesis",
            "claims": [{"claim": "demand resilient", "evidence_id": "assessment:semis"}],
            "bear_case": ["multiple compression"],
            "evidence_refs": ["assessment:semis", "regime"],
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
        return {
            "status": "WATCH",
            "rationale": "gates passed; tracking only",
            "bear_case": ["competition"],
            "risks": ["valuation"],
            "invalidation_conditions": ["QA regresses"],
            "evidence_refs": ["assessment:semis"],
        }
    raise ValueError(f"no mock for {role}")
