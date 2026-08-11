from __future__ import annotations

import hashlib
import json
from typing import Any

from app.agents.claim_support import deterministic_claim_verdicts
from app.research.model_capabilities import load_recorded_model_capabilities
from app.research.openai_responses import ResponsesResult, resolve_requested_model

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
        self.allowed_models = (
            set(allowed_models) if allowed_models is not None else load_recorded_model_capabilities()
        )

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
        resolved = resolve_requested_model(model, available=self.allowed_models)
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


def _grounded_claims(packet: dict[str, Any]) -> list[dict[str, str]]:
    evidence = [e for e in (packet.get("evidence") or []) if isinstance(e, dict)]
    claims: list[dict[str, str]] = []
    for ev in evidence:
        eid = str(ev.get("evidence_id") or "").strip()
        if not eid:
            continue
        payload = ev.get("payload") if isinstance(ev.get("payload"), dict) else {}
        if "regime" in payload:
            claims.append({"claim": f"regime is {payload.get('regime')}", "evidence_id": eid})
        elif payload.get("industry_id") is not None:
            ind = str(payload.get("industry_id"))
            score = payload.get("overall_score")
            if score is not None:
                claims.append({"claim": f"{ind} overall_score {score}", "evidence_id": eid})
            else:
                claims.append({"claim": json.dumps(payload, ensure_ascii=False, sort_keys=True), "evidence_id": eid})
        else:
            blob = json.dumps(payload, ensure_ascii=False, sort_keys=True) if payload else eid
            claims.append({"claim": blob, "evidence_id": eid})
    if not claims:
        allowed = list(packet.get("allowed_evidence_ids") or [])
        primary = allowed[0] if allowed else "regime"
        claims = [{"claim": "regime is expansion", "evidence_id": primary}]
    return claims


def _weak_output(role: str, packet: dict[str, Any]) -> dict[str, Any]:
    """Schema-valid but gate-failing output when high-stakes effort is too low."""
    if role == "research_qa_agent":
        return {
            "status": "FAIL",
            "failed_claims": ["insufficient_reasoning_effort"],
            "warnings": [],
            "claim_verdicts": [],
        }
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
        claims = _grounded_claims(packet)
        refs = list(dict.fromkeys([c["evidence_id"] for c in claims] + allowed[:3])) or [primary]
        return {
            "synthesis": "mock synthesis using allowed evidence only",
            "claims": claims,
            "bear_case": ["multiple compression"],
            "evidence_refs": refs,
            "unsupported_or_missing": [],
        }
    if role == "research_qa_agent":
        research = packet.get("research_agent") or {}
        claims = packet.get("claims") if packet.get("claims") is not None else research.get("claims") or []
        evidence = packet.get("evidence") or []
        verdicts = deterministic_claim_verdicts({"claims": claims}, evidence)
        public = [
            {"claim_id": v["claim_id"], "evidence_id": v["evidence_id"], "support": v["support"]}
            for v in verdicts
        ]
        failed = [v["claim_id"] for v in verdicts if v["support"] != "SUPPORTED"]
        return {
            "status": "PASS" if not failed else "FAIL",
            "failed_claims": failed,
            "warnings": [],
            "claim_verdicts": public,
        }
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
