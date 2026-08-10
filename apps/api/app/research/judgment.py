from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import psycopg

from app.llm_profiles import load_llm_profiles
from app.research.company_research import ResponsesClient
from app.research.openai_responses import ModelUnavailableError
from app.research.schema_validate import load_schema, validate_against_schema
from app.settings import Settings, get_settings

PROMPT_PATH = Path(__file__).resolve().parents[4] / "config" / "prompts" / "final_judgment.v0.1.txt"
PROMPT_VERSION = "final-judgment-prompt-v0.1"
SCHEMA_VERSION = "final-judgment-output-v0.1"


class JudgmentPolicyError(RuntimeError):
    pass


def _hash(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def enforce_judgment_policy(qa_status: str, judgment: dict[str, Any], packet: dict[str, Any]) -> None:
    if judgment.get("status") == "SELECTED" and qa_status == "FAIL":
        raise JudgmentPolicyError("QA FAIL cannot be SELECTED")
    if judgment.get("status") == "SELECTED":
        for key in ("bear_case", "risks", "invalidation_conditions"):
            if not judgment.get(key):
                raise JudgmentPolicyError(f"SELECTED requires non-empty {key}")
    evidence_ids = {e.get("evidence_id") for e in (packet.get("evidence") or []) if isinstance(e, dict)}
    for ref in judgment.get("key_evidence_refs") or []:
        if ref not in evidence_ids:
            raise JudgmentPolicyError(f"judgment evidence ref not in packet: {ref}")


def run_final_judgment(
    conn: psycopg.Connection,
    *,
    packet: dict[str, Any],
    qa_id: str,
    qa_status: str,
    judgment_output: dict[str, Any] | None = None,
    client: ResponsesClient | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Persist immutable judgment. Prefer provided judgment_output (tests); else call client."""
    settings = settings or get_settings()
    profiles = load_llm_profiles()
    role = profiles.final_judgment
    schema = load_schema("final_judgment_output.schema.json")

    execution_id = str(uuid4())
    started = datetime.now(timezone.utc)
    input_hash = _hash({"packet": packet, "qa_id": qa_id, "qa_status": qa_status})
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into llm_executions (
              execution_id, run_id, security_id, agent_role, prompt_version, llm_profile_version,
              requested_model, reasoning_effort, input_hash, schema_version, status, started_at
            ) values (%s,%s,%s,'final_judgment',%s,%s,%s,%s,%s,%s,'running',%s)
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

    resolved = role.model
    response_id = None
    try:
        if judgment_output is None:
            if client is None:
                raise JudgmentPolicyError("judgment_output or client required")
            result = client.create_structured(
                model=role.model,
                reasoning_effort=role.reasoning_effort,
                system_prompt=PROMPT_PATH.read_text(encoding="utf-8"),
                user_payload={"packet": packet, "qa_status": qa_status},
                output_schema=schema,
                schema_name="final_judgment_output",
            )
            if result.resolved_model != role.model:
                raise ModelUnavailableError(
                    f"resolved model {result.resolved_model!r} != requested {role.model!r}"
                )
            judgment_output = json.loads(result.output_text)
            resolved = result.resolved_model
            response_id = result.response_id
        validate_against_schema(judgment_output, schema)
        enforce_judgment_policy(qa_status, judgment_output, packet)
    except (ModelUnavailableError, JudgmentPolicyError, ValueError) as e:
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

    with conn.cursor() as cur:
        cur.execute(
            "select total_score from quant_scores where run_id=%s and security_id=%s",
            (packet["run_id"], packet["security_id"]),
        )
        qrow = cur.fetchone()
        quant_score = float(qrow[0]) if qrow else None
        prices = ((packet.get("price_metrics") or {}).get("series") or [])
        selection_price = float(prices[-1]["close"]) if prices else None

    immutable_hash = _hash(
        {
            "run_id": packet["run_id"],
            "security_id": packet["security_id"],
            "qa_id": qa_id,
            "judgment": judgment_output,
        }
    )
    judgment_id = str(uuid4())
    out_hash = _hash(judgment_output)
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
            insert into judgments (
              judgment_id, run_id, security_id, status, selection_price, quant_score,
              thesis, bear_case, risks, invalidation_conditions, evidence_quality,
              data_completeness, uncertainty, final_execution_id, qa_id, output_json, immutable_hash
            ) values (
              %s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s::jsonb,%s
            )
            """,
            (
                judgment_id,
                packet["run_id"],
                packet["security_id"],
                judgment_output["status"],
                selection_price,
                quant_score,
                judgment_output["thesis"],
                json.dumps(judgment_output["bear_case"]),
                json.dumps(judgment_output["risks"]),
                json.dumps(judgment_output["invalidation_conditions"]),
                judgment_output["evidence_quality"],
                judgment_output["data_completeness"],
                judgment_output["uncertainty"],
                execution_id,
                qa_id,
                json.dumps(judgment_output),
                immutable_hash,
            ),
        )
    conn.commit()
    return {
        "judgment_id": judgment_id,
        "execution_id": execution_id,
        "status": judgment_output["status"],
        "immutable_hash": immutable_hash,
        "requested_model": role.model,
        "resolved_model": resolved,
        "reasoning_effort": role.reasoning_effort,
        "output": judgment_output,
    }
