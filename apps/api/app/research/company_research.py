from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

import psycopg

from app.llm_profiles import load_llm_profiles
from app.research.openai_responses import ModelUnavailableError, OpenAIResponsesClient, ResponsesResult
from app.research.packet import load_research_limits, persist_packet
from app.research.schema_validate import load_schema, validate_against_schema
from app.settings import Settings, get_settings

PROMPT_PATH = Path(__file__).resolve().parents[4] / "config" / "prompts" / "company_research.v0.1.txt"
OUTPUT_SCHEMA_VERSION = "company-analysis-output-v0.1"


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


def run_company_research(
    conn: psycopg.Connection,
    *,
    packet: dict[str, Any],
    client: ResponsesClient | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    profiles = load_llm_profiles()
    role = profiles.company_research
    limits = load_research_limits()
    prompt_version = str(limits.get("company_research_prompt_version") or "company-research-prompt-v0.1")
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    output_schema = load_schema("company_analysis_output.schema.json")
    # Responses API json_schema often requires additionalProperties explicitly
    if "additionalProperties" not in output_schema:
        output_schema = {**output_schema, "additionalProperties": False}

    persisted = persist_packet(conn, packet=packet)
    input_hash = persisted["input_hash"]
    execution_id = str(uuid4())
    started = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            """
            insert into llm_executions (
              execution_id, run_id, security_id, agent_role, prompt_version, llm_profile_version,
              requested_model, reasoning_effort, input_hash, schema_version, status, started_at
            ) values (%s,%s,%s,'company_research',%s,%s,%s,%s,%s,%s,'running',%s)
            """,
            (
                execution_id,
                packet["run_id"],
                packet["security_id"],
                prompt_version,
                profiles.version,
                role.model,
                role.reasoning_effort,
                input_hash,
                OUTPUT_SCHEMA_VERSION,
                started,
            ),
        )
    conn.commit()

    active = client or OpenAIResponsesClient(settings)
    try:
        result = active.create_structured(
            model=role.model,
            reasoning_effort=role.reasoning_effort,
            system_prompt=system_prompt,
            user_payload=packet,
            output_schema=output_schema,
            schema_name="company_analysis_output",
        )
        if result.resolved_model != role.model:
            raise ModelUnavailableError(
                f"resolved model {result.resolved_model!r} != requested {role.model!r} (no silent fallback)"
            )
        output = json.loads(result.output_text)
        validate_against_schema(output, load_schema("company_analysis_output.schema.json"))
        # require unsupported_or_missing explicit list (may be empty)
        if "unsupported_or_missing" not in output:
            raise ValueError("unsupported_or_missing missing")
        out_hash = _hash(output)
        research_id = str(uuid4())
        with conn.cursor() as cur:
            cur.execute(
                """
                update llm_executions set
                  status='succeeded',
                  resolved_model=%s,
                  response_id=%s,
                  output_hash=%s,
                  token_usage=%s::jsonb,
                  completed_at=%s
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
                insert into ai_research (research_id, execution_id, run_id, security_id, output_json, output_hash)
                values (%s,%s,%s,%s,%s::jsonb,%s)
                """,
                (
                    research_id,
                    execution_id,
                    packet["run_id"],
                    packet["security_id"],
                    json.dumps(output),
                    out_hash,
                ),
            )
        conn.commit()
        return {
            "execution_id": execution_id,
            "research_id": research_id,
            "requested_model": role.model,
            "resolved_model": result.resolved_model,
            "reasoning_effort": role.reasoning_effort,
            "llm_profile_version": profiles.version,
            "prompt_version": prompt_version,
            "input_hash": input_hash,
            "output_hash": out_hash,
            "output": output,
        }
    except ModelUnavailableError as e:
        with conn.cursor() as cur:
            cur.execute(
                """
                update llm_executions set status='failed', error_code='model_unavailable',
                  completed_at=%s where execution_id=%s
                """,
                (datetime.now(timezone.utc), execution_id),
            )
        conn.commit()
        raise
    except Exception as e:
        with conn.cursor() as cur:
            cur.execute(
                """
                update llm_executions set status='failed', error_code=%s, completed_at=%s
                where execution_id=%s
                """,
                (type(e).__name__[:80], datetime.now(timezone.utc), execution_id),
            )
        conn.commit()
        raise
