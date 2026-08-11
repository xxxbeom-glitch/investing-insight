from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

import psycopg

from app.agents.profiles import MultiAgentProfiles, load_multiagent_profiles
from app.research.openai_responses import ModelUnavailableError, OpenAIResponsesClient, ResponsesResult
from app.research.schema_validate import load_schema, validate_against_schema
from app.settings import Settings, get_settings

PROMPT_DIR = Path(__file__).resolve().parents[4] / "config" / "prompts" / "agents"

ROLE_SCHEMA = {
    "market_agent": ("agent_market_output.schema.json", "agent-market-output-v0.1"),
    "industry_agent": ("agent_industry_output.schema.json", "agent-industry-output-v0.1"),
    "company_agent": ("agent_company_output.schema.json", "agent-company-output-v0.1"),
    "event_agent": ("agent_event_output.schema.json", "agent-event-output-v0.1"),
    "research_agent": ("agent_research_output.schema.json", "agent-research-output-v0.1"),
    "research_qa_agent": ("agent_research_qa_output.schema.json", "agent-research-qa-output-v0.1"),
    "adversarial_agent": ("agent_adversarial_output.schema.json", "agent-adversarial-output-v0.1"),
    "final_selector_agent": ("agent_final_selector_output.schema.json", "agent-final-selector-output-v0.1"),
}


class ResponsesClient(Protocol):
    def create_structured(
        self,
        *,
        model: str,
        reasoning_effort: str,
        system_prompt: str,
        user_payload: dict[str, Any],
        output_schema: dict[str, Any],
        schema_name: str,
    ) -> ResponsesResult: ...


def _hash(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()



def build_role_packet(
    *,
    agent_role: str,
    run_id: str,
    snapshot_id: str,
    frozen_context: dict[str, Any],
    security_id: str | None = None,
    ticker: str | None = None,
    prior_outputs: dict[str, Any] | None = None,
    evidence_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Role-minimal input — same snapshot baseline, no free-form chat history."""
    prior = prior_outputs or {}
    bundle = evidence_bundle or {}
    allowed = list(bundle.get("allowed_evidence_ids") or [])
    base = {
        "run_id": run_id,
        "snapshot_id": snapshot_id,
        "agent_role": agent_role,
    }
    if agent_role == "market_agent":
        return {
            **base,
            "regime": frozen_context.get("regime"),
            "macro_inputs": (frozen_context.get("regime") or {}).get("inputs"),
            "allowed_evidence_ids": [x for x in allowed if x == "regime"],
        }
    if agent_role == "industry_agent":
        return {
            **base,
            "assessments": frozen_context.get("assessments"),
            "regime": (frozen_context.get("regime") or {}).get("regime"),
            "market_agent": prior.get("market_agent"),
            "allowed_evidence_ids": [x for x in allowed if x.startswith("assessment") or x == "regime"],
        }
    if agent_role == "company_agent":
        return {
            **base,
            "security_id": security_id,
            "ticker": ticker,
            "union_member": next(
                (
                    m
                    for m in (frozen_context.get("union") or {}).get("members") or []
                    if m.get("security_id") == security_id or m.get("ticker") == ticker
                ),
                {"ticker": ticker, "security_id": security_id},
            ),
            "industry_agent": prior.get("industry_agent"),
            "prices": bundle.get("prices") or [],
            "financial_facts": bundle.get("financial_facts") or [],
            "quant": bundle.get("quant"),
            "allowed_evidence_ids": allowed,
        }
    if agent_role == "event_agent":
        return {
            **base,
            "security_id": security_id,
            "ticker": ticker,
            "company_agent": prior.get("company_agent"),
            "filings_or_events": bundle.get("filings_or_events") or [],
            "financial_facts": bundle.get("financial_facts") or [],
            "allowed_evidence_ids": [x for x in allowed if x.startswith("filing") or x.startswith("fact")],
        }
    if agent_role == "research_agent":
        return {
            **base,
            "security_id": security_id,
            "ticker": ticker,
            "market_agent": prior.get("market_agent"),
            "industry_agent": prior.get("industry_agent"),
            "company_agent": prior.get("company_agent"),
            "event_agent": prior.get("event_agent"),
            "evidence": bundle.get("evidence") or [],
            "allowed_evidence_ids": allowed,
        }
    if agent_role == "research_qa_agent":
        research = prior.get("research_agent") or {}
        return {
            **base,
            "research_agent": research,
            "claims": research.get("claims") or [],
            "evidence": bundle.get("evidence") or [],
            "allowed_evidence_ids": allowed,
        }
    if agent_role == "adversarial_agent":
        return {
            **base,
            "research_agent": prior.get("research_agent"),
            "research_qa_agent": prior.get("research_qa_agent"),
            "evidence": bundle.get("evidence") or [],
            "allowed_evidence_ids": allowed,
        }
    if agent_role == "final_selector_agent":
        from app.agents.final_gate import approved_claim_catalog

        catalog = approved_claim_catalog(
            prior.get("research_agent"),
            prior.get("adversarial_agent"),
            allowed_evidence_ids=allowed,
        )
        return {
            **base,
            "security_id": security_id,
            "ticker": ticker,
            "research_agent": prior.get("research_agent"),
            "research_qa_agent": prior.get("research_qa_agent"),
            "adversarial_agent": prior.get("adversarial_agent"),
            "approved_claims": catalog,
            "allowed_evidence_ids": allowed,
        }
    raise ValueError(f"unknown agent_role: {agent_role}")


def _system_prompt(agent_role: str) -> str:
    path = PROMPT_DIR / f"{agent_role}.v0.1.txt"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    raise FileNotFoundError(f"missing role prompt: {path}")


def run_agent_role(
    conn: psycopg.Connection,
    *,
    multi_agent_run_id: str,
    agent_role: str,
    packet: dict[str, Any],
    client: ResponsesClient | None = None,
    settings: Settings | None = None,
    profiles: MultiAgentProfiles | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    profiles = profiles or load_multiagent_profiles()
    role_prof = getattr(profiles, agent_role)
    schema_file, schema_version = ROLE_SCHEMA[agent_role]
    output_schema = load_schema(schema_file)
    if "additionalProperties" not in output_schema:
        output_schema = {**output_schema, "additionalProperties": False}

    input_hash = _hash(packet)
    execution_id = str(uuid4())
    started = datetime.now(timezone.utc)
    security_id = packet.get("security_id")
    run_id = packet["run_id"]
    snapshot_id = packet["snapshot_id"]

    with conn.cursor() as cur:
        cur.execute(
            """
            insert into llm_executions (
              execution_id, run_id, security_id, agent_role, prompt_version, llm_profile_version,
              requested_model, reasoning_effort, input_hash, schema_version, status, started_at
            ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'running',%s)
            """,
            (
                execution_id,
                run_id,
                security_id,
                agent_role,
                f"{agent_role}-prompt-v0.1",
                profiles.version,
                role_prof.model,
                role_prof.reasoning_effort,
                input_hash,
                schema_version,
                started,
            ),
        )
    conn.commit()

    active = client or OpenAIResponsesClient(settings)
    try:
        result = active.create_structured(
            model=role_prof.model,
            reasoning_effort=role_prof.reasoning_effort,
            system_prompt=_system_prompt(agent_role),
            user_payload=packet,
            output_schema=output_schema,
            schema_name=agent_role,
        )
        if result.resolved_model != role_prof.model:
            raise ModelUnavailableError(
                f"resolved model {result.resolved_model!r} != requested {role_prof.model!r}"
            )
        output = json.loads(result.output_text)
        validate_against_schema(output, load_schema(schema_file))
        out_hash = _hash(output)
        output_id = str(uuid4())
        with conn.cursor() as cur:
            cur.execute(
                """
                update llm_executions set
                  status='succeeded', resolved_model=%s, response_id=%s, output_hash=%s,
                  token_usage=%s::jsonb, completed_at=%s
                where execution_id=%s
                """,
                (
                    result.resolved_model,
                    result.response_id,
                    out_hash,
                    json.dumps(result.token_usage) if result.token_usage else None,
                    datetime.now(timezone.utc),
                    execution_id,
                ),
            )
            cur.execute(
                """
                insert into agent_outputs (
                  output_id, multi_agent_run_id, run_id, snapshot_id, security_id,
                  agent_role, execution_id, schema_version, input_hash, output_json, output_hash
                ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
                """,
                (
                    output_id,
                    multi_agent_run_id,
                    run_id,
                    snapshot_id,
                    security_id,
                    agent_role,
                    execution_id,
                    schema_version,
                    input_hash,
                    json.dumps(output),
                    out_hash,
                ),
            )
        conn.commit()
        return {
            "output_id": output_id,
            "execution_id": execution_id,
            "agent_role": agent_role,
            "snapshot_id": snapshot_id,
            "run_id": run_id,
            "output": output,
            "output_hash": out_hash,
        }
    except Exception as exc:  # noqa: BLE001
        with conn.cursor() as cur:
            cur.execute(
                """
                update llm_executions set status='failed', error_code=%s, completed_at=%s
                where execution_id=%s
                """,
                (type(exc).__name__, datetime.now(timezone.utc), execution_id),
            )
        conn.commit()
        raise


class GateBlockedError(RuntimeError):
    pass


def record_gate(
    conn: psycopg.Connection,
    *,
    multi_agent_run_id: str,
    gate_type: str,
    status: str,
    reasons: list[str],
    source_output_id: str | None,
) -> dict[str, Any]:
    gate_id = str(uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into agent_gates (gate_id, multi_agent_run_id, gate_type, status, reasons, source_output_id)
            values (%s,%s,%s,%s,%s::jsonb,%s)
            """,
            (gate_id, multi_agent_run_id, gate_type, status, json.dumps(reasons), source_output_id),
        )
        if status == "FAIL":
            cur.execute(
                """
                update multi_agent_runs
                set status='blocked', block_reason=%s, completed_at=%s
                where multi_agent_run_id=%s::uuid
                """,
                (f"{gate_type}:{','.join(reasons)[:200]}", datetime.now(timezone.utc), multi_agent_run_id),
            )
    conn.commit()
    return {"gate_id": gate_id, "gate_type": gate_type, "status": status, "reasons": reasons}



def evaluate_research_qa_gate(
    output: dict[str, Any],
    *,
    research_output: dict[str, Any] | None = None,
    allowed_evidence_ids: list[str] | set[str] | None = None,
) -> tuple[str, list[str]]:
    from app.agents.evidence import validate_research_evidence_ids

    if research_output is not None and allowed_evidence_ids is not None:
        det_status, det_reasons = validate_research_evidence_ids(research_output, allowed_evidence_ids)
        if det_status != "PASS":
            return "FAIL", det_reasons
    status = output.get("status")
    reasons = list(output.get("failed_claims") or [])
    if status != "PASS":
        return "FAIL", reasons or ["research_qa_status_not_pass"]
    return "PASS", []


def evaluate_adversarial_gate(output: dict[str, Any]) -> tuple[str, list[str]]:
    status = output.get("status")
    blockers = list(output.get("gate_blockers") or [])
    if status != "PASS":
        return "FAIL", blockers or ["adversarial_status_not_pass"]
    if blockers:
        return "FAIL", blockers
    return "PASS", []
