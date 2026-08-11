"""V1→V2 governance (Post-MVP M06) — machine-verifiable replay/holdout required."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg

ARTIFACT_TYPES = {"score_rule", "prompt", "model", "llm_profile", "quant_rule", "other"}
STATUSES = {"draft", "proposed", "approved", "rejected", "frozen"}
PASS_STATUSES = {"PASS", "pass", "passed", "PASSED"}


class GovernanceError(RuntimeError):
    pass


def _require_eval_pass(label: str, eval_obj: dict[str, Any] | None) -> None:
    if not isinstance(eval_obj, dict):
        raise GovernanceError(f"{label} eval artifact required (dict)")
    status = str(eval_obj.get("status") or "")
    if status not in PASS_STATUSES:
        raise GovernanceError(f"{label} status must be PASS, got {status!r}")
    if not eval_obj.get("dataset_id") and not eval_obj.get("snapshot_id") and not eval_obj.get("run_id"):
        raise GovernanceError(f"{label} must include dataset_id or snapshot_id or run_id")
    if "metrics" not in eval_obj:
        raise GovernanceError(f"{label} must include metrics object")


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


def attach_eval_artifacts(
    conn: psycopg.Connection,
    proposal_id: str,
    *,
    replay_eval: dict[str, Any],
    holdout_eval: dict[str, Any],
) -> dict[str, Any]:
    """Persist machine-verifiable replay/holdout results before approve."""
    _require_eval_pass("replay", replay_eval)
    _require_eval_pass("holdout", holdout_eval)
    with conn.cursor() as cur:
        cur.execute(
            "select status from change_proposals where proposal_id=%s::uuid",
            (proposal_id,),
        )
        row = cur.fetchone()
        if not row:
            raise GovernanceError("proposal not found")
        if row[0] not in {"draft", "proposed"}:
            raise GovernanceError(f"cannot attach evals from status={row[0]}")
        cur.execute(
            """
            update change_proposals set
              replay_eval=%s::jsonb,
              holdout_eval=%s::jsonb,
              replay_status=%s,
              holdout_status=%s,
              updated_at=now()
            where proposal_id=%s::uuid
            """,
            (
                json.dumps(replay_eval),
                json.dumps(holdout_eval),
                str(replay_eval.get("status")),
                str(holdout_eval.get("status")),
                proposal_id,
            ),
        )
    conn.commit()
    return {
        "proposal_id": proposal_id,
        "replay_status": replay_eval.get("status"),
        "holdout_status": holdout_eval.get("status"),
    }


def approve_proposal(
    conn: psycopg.Connection,
    proposal_id: str,
    *,
    replay_notes: str = "",
    holdout_notes: str = "",
    approver: str = "operator",
    replay_eval: dict[str, Any] | None = None,
    holdout_eval: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Approve only when replay+holdout evals are PASS (notes alone insufficient)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            select status, approval_log, replay_eval, holdout_eval, replay_status, holdout_status
            from change_proposals where proposal_id=%s::uuid
            """,
            (proposal_id,),
        )
        row = cur.fetchone()
        if not row:
            raise GovernanceError("proposal not found")
        if row[0] != "proposed":
            raise GovernanceError(f"cannot approve from status={row[0]}")

        stored_replay = row[2] if isinstance(row[2], dict) else (json.loads(row[2]) if row[2] else None)
        stored_holdout = row[3] if isinstance(row[3], dict) else (json.loads(row[3]) if row[3] else None)
        replay = replay_eval or stored_replay
        holdout = holdout_eval or stored_holdout
        _require_eval_pass("replay", replay)
        _require_eval_pass("holdout", holdout)

        # Notes are optional annotations only — cannot substitute for PASS evals
        log = row[1] if isinstance(row[1], list) else json.loads(row[1] or "[]")
        log.append(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "action": "approve",
                "by": approver,
                "replay_status": replay.get("status"),
                "holdout_status": holdout.get("status"),
                "replay_notes": (replay_notes or "")[:500],
                "holdout_notes": (holdout_notes or "")[:500],
            }
        )
        cur.execute(
            """
            update change_proposals set
              status='approved',
              replay_notes=%s,
              holdout_notes=%s,
              replay_eval=%s::jsonb,
              holdout_eval=%s::jsonb,
              replay_status=%s,
              holdout_status=%s,
              approval_log=%s::jsonb,
              updated_at=now()
            where proposal_id=%s::uuid
            """,
            (
                (replay_notes or "").strip(),
                (holdout_notes or "").strip(),
                json.dumps(replay),
                json.dumps(holdout),
                str(replay.get("status")),
                str(holdout.get("status")),
                json.dumps(log),
                proposal_id,
            ),
        )
    conn.commit()
    return {"proposal_id": proposal_id, "status": "approved"}


def freeze_proposal(conn: psycopg.Connection, proposal_id: str, *, by: str = "operator") -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select status, approval_log, to_version, replay_status, holdout_status
            from change_proposals where proposal_id=%s::uuid
            """,
            (proposal_id,),
        )
        row = cur.fetchone()
        if not row:
            raise GovernanceError("proposal not found")
        if row[0] != "approved":
            raise GovernanceError("freeze requires approved status")
        if str(row[3]) not in PASS_STATUSES or str(row[4]) not in PASS_STATUSES:
            raise GovernanceError("freeze requires replay_status and holdout_status PASS")
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
