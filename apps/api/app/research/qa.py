from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import psycopg

from app.llm_profiles import load_llm_profiles
from app.research.claim_check import deterministic_qa
from app.research.company_research import ResponsesClient
from app.research.openai_responses import ModelUnavailableError
from app.research.schema_validate import load_schema, validate_against_schema
from app.settings import Settings, get_settings

PROMPT_PATH = Path(__file__).resolve().parents[4] / "config" / "prompts" / "research_qa.v0.1.txt"
PROMPT_VERSION = "research-qa-prompt-v0.1"
SCHEMA_VERSION = "research-qa-output-v0.1"


def _hash(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def run_research_qa(
    conn: psycopg.Connection,
    *,
    packet: dict[str, Any],
    research_id: str,
    research_output: dict[str, Any],
    client: ResponsesClient | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Deterministic claim check is authoritative; optional LLM may only tighten severity."""
    _ = settings or get_settings()
    profiles = load_llm_profiles()
    role = profiles.research_qa
    base = deterministic_qa(packet, research_output)
    validate_against_schema(base, load_schema("research_qa_output.schema.json"))

    execution_id = str(uuid4())
    started = datetime.now(timezone.utc)
    input_hash = _hash({"packet": packet, "research": research_output})
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into llm_executions (
              execution_id, run_id, security_id, agent_role, prompt_version, llm_profile_version,
              requested_model, reasoning_effort, input_hash, schema_version, status, started_at
            ) values (%s,%s,%s,'research_qa',%s,%s,%s,%s,%s,%s,'running',%s)
            """,
            (
                execution_id,
                packet["run_id"],
                packet["security_id"],
                PROMPT_VERSION,
                profiles.version,
                role.model,
                role.reasoning_effort,
                input_hash,
                SCHEMA_VERSION,
                started,
            ),
        )
    conn.commit()

    output = base
    resolved = role.model
    response_id = None
    try:
        if client is not None:
            result = client.create_structured(
                model=role.model,
                reasoning_effort=role.reasoning_effort,
                system_prompt=PROMPT_PATH.read_text(encoding="utf-8"),
                user_payload={"packet": packet, "research": research_output, "deterministic_qa": base},
                output_schema=load_schema("research_qa_output.schema.json"),
                schema_name="research_qa_output",
            )
            if result.resolved_model != role.model:
                raise ModelUnavailableError(
                    f"resolved model {result.resolved_model!r} != requested {role.model!r}"
                )
            llm_out = json.loads(result.output_text)
            validate_against_schema(llm_out, load_schema("research_qa_output.schema.json"))
            resolved = result.resolved_model
            response_id = result.response_id
            if base["status"] == "FAIL":
                output = base
            elif llm_out["status"] == "FAIL":
                output = llm_out
            elif base["status"] == "PASS_WITH_WARNING":
                output = {
                    **llm_out,
                    "status": "PASS_WITH_WARNING",
                    "warnings": sorted(set((llm_out.get("warnings") or []) + base["warnings"])),
                }
            else:
                output = llm_out
    except ModelUnavailableError:
        with conn.cursor() as cur:
            cur.execute(
                """
                update llm_executions set status='failed', error_code='model_unavailable', completed_at=%s
                where execution_id=%s
                """,
                (datetime.now(timezone.utc), execution_id),
            )
        conn.commit()
        raise

    out_hash = _hash(output)
    qa_id = str(uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            update llm_executions set
              status='succeeded', resolved_model=%s, response_id=%s, output_hash=%s, completed_at=%s
            where execution_id=%s
            """,
            (resolved, response_id, out_hash, datetime.now(timezone.utc), execution_id),
        )
        cur.execute(
            """
            insert into research_qa (
              qa_id, execution_id, research_id, status, failed_claims, warnings, output_json
            ) values (%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb)
            """,
            (
                qa_id,
                execution_id,
                research_id,
                output["status"],
                json.dumps(output.get("failed_claims") or []),
                json.dumps(output.get("warnings") or []),
                json.dumps(output),
            ),
        )
    conn.commit()
    return {
        "qa_id": qa_id,
        "execution_id": execution_id,
        "status": output["status"],
        "output": output,
        "requested_model": role.model,
        "resolved_model": resolved,
        "reasoning_effort": role.reasoning_effort,
        "llm_profile_version": profiles.version,
    }
