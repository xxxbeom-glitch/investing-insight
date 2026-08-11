"""V1→V2 governance (Post-MVP M06)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg

ARTIFACT_TYPES = {"score_rule", "prompt", "model", "llm_profile", "quant_rule", "other"}
STATUSES = {"draft", "proposed", "approved", "rejected", "frozen"}


class GovernanceError(RuntimeError):
    pass


def create_proposal(
    conn: psycopg.Connection,
    *,
    artifact_type: str,
    artifact_ref: str,
    to_version: str,
    rationale: str,
    from_version: str | None = None,
) -> dict[str, Any]:
    if artifact_type not in ARTIFACT_TYPES:
        raise GovernanceError(f"invalid artifact_type: {artifact_type}")
    if not rationale.strip() or not to_version.strip():
        raise GovernanceError("rationale and to_version required")
    pid = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into change_proposals (
              proposal_id, artifact_type, artifact_ref, from_version, to_version,
              rationale, status
            ) values (%s,%s,%s,%s,%s,%s,'draft')
            """,
            (pid, artifact_type, artifact_ref, from_version, to_version, rationale.strip()),
        )
    conn.commit()
    return {"proposal_id": pid, "status": "draft"}


def submit_proposal(conn: psycopg.Connection, proposal_id: str) -> dict[str, Any]:
    return _set_status(conn, proposal_id, "proposed", require_from={"draft"})


def approve_proposal(
    conn: psycopg.Connection,
    proposal_id: str,
    *,
    replay_notes: str,
    holdout_notes: str,
    approver: str = "operator",
) -> dict[str, Any]:
    if not replay_notes.strip() or not holdout_notes.strip():
        raise GovernanceError("replay_notes and holdout_notes required before approve")
    with conn.cursor() as cur:
        cur.execute(
            "select status, approval_log from change_proposals where proposal_id=%s::uuid",
            (proposal_id,),
        )
        row = cur.fetchone()
        if not row:
            raise GovernanceError("proposal not found")
        if row[0] != "proposed":
            raise GovernanceError(f"cannot approve from status={row[0]}")
        log = row[1] if isinstance(row[1], list) else json.loads(row[1] or "[]")
        log.append(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "action": "approve",
                "by": approver,
                "replay_notes": replay_notes.strip()[:500],
                "holdout_notes": holdout_notes.strip()[:500],
            }
        )
        cur.execute(
            """
            update change_proposals set
              status='approved',
              replay_notes=%s,
              holdout_notes=%s,
              approval_log=%s::jsonb,
              updated_at=now()
            where proposal_id=%s::uuid
            """,
            (replay_notes.strip(), holdout_notes.strip(), json.dumps(log), proposal_id),
        )
    conn.commit()
    return {"proposal_id": proposal_id, "status": "approved"}


def freeze_proposal(conn: psycopg.Connection, proposal_id: str, *, by: str = "operator") -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            "select status, approval_log, to_version from change_proposals where proposal_id=%s::uuid",
            (proposal_id,),
        )
        row = cur.fetchone()
        if not row:
            raise GovernanceError("proposal not found")
        if row[0] != "approved":
            raise GovernanceError("freeze requires approved status")
        log = row[1] if isinstance(row[1], list) else json.loads(row[1] or "[]")
        log.append({"at": datetime.now(timezone.utc).isoformat(), "action": "freeze", "by": by})
        cur.execute(
            """
            update change_proposals set status='frozen', approval_log=%s::jsonb, updated_at=now()
            where proposal_id=%s::uuid
            """,
            (json.dumps(log), proposal_id),
        )
    conn.commit()
    return {"proposal_id": proposal_id, "status": "frozen", "frozen_version": row[2]}


def _set_status(
    conn: psycopg.Connection,
    proposal_id: str,
    new_status: str,
    *,
    require_from: set[str],
) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute("select status from change_proposals where proposal_id=%s::uuid", (proposal_id,))
        row = cur.fetchone()
        if not row:
            raise GovernanceError("proposal not found")
        if row[0] not in require_from:
            raise GovernanceError(f"cannot move to {new_status} from {row[0]}")
        cur.execute(
            "update change_proposals set status=%s, updated_at=now() where proposal_id=%s::uuid",
            (new_status, proposal_id),
        )
    conn.commit()
    return {"proposal_id": proposal_id, "status": new_status}
