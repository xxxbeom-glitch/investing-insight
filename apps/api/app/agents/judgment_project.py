"""Project gate-passed Final Selector into immutable judgments (ER-P1-03)."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import uuid4

import psycopg


def _hash(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def project_final_selector_to_judgment(
    conn: psycopg.Connection,
    *,
    multi_agent_run_id: str,
    run_id: str,
    security_id: str,
    final_output: dict[str, Any],
    source_agent_output_id: str,
) -> dict[str, Any]:
    status = str(final_output.get("status") or "WATCH").upper()
    if status not in {"SELECTED", "WATCH", "REJECT"}:
        status = "WATCH"
    thesis = str(final_output.get("rationale") or final_output.get("thesis") or "")
    bear = final_output.get("bear_case") or []
    risks = final_output.get("risks") or []
    inval = final_output.get("invalidation_conditions") or []
    if isinstance(bear, str):
        bear = [bear]
    if isinstance(risks, str):
        risks = [risks]
    if isinstance(inval, str):
        inval = [inval]
    payload = {
        "source": "multi_agent_final_selector",
        "multi_agent_run_id": multi_agent_run_id,
        "output": final_output,
    }
    immutable_hash = _hash(payload)
    judgment_id = str(uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into judgments (
              judgment_id, run_id, security_id, status, selection_price, quant_score,
              thesis, bear_case, risks, invalidation_conditions,
              evidence_quality, data_completeness, uncertainty,
              final_execution_id, qa_id, output_json, immutable_hash,
              multi_agent_run_id, source_agent_output_id
            ) values (
              %s,%s,%s,%s,null,null,%s,%s::jsonb,%s::jsonb,%s::jsonb,
              %s,%s,%s,null,null,%s::jsonb,%s,%s,%s
            )
            on conflict (run_id, security_id, immutable_hash) do nothing
            returning judgment_id::text
            """,
            (
                judgment_id,
                run_id,
                security_id,
                status,
                thesis,
                json.dumps(bear),
                json.dumps(risks),
                json.dumps(inval),
                "multi_agent",
                0.0,
                "multi_agent",
                json.dumps(payload),
                immutable_hash,
                multi_agent_run_id,
                source_agent_output_id,
            ),
        )
        row = cur.fetchone()
        if not row:
            cur.execute(
                """
                select judgment_id::text from judgments
                where run_id=%s::uuid and security_id=%s::uuid and immutable_hash=%s
                """,
                (run_id, security_id, immutable_hash),
            )
            row = cur.fetchone()
    conn.commit()
    return {"judgment_id": row[0], "status": status, "immutable_hash": immutable_hash}
