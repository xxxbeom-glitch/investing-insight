"""V1→V2 governance (Post-MVP M06) — machine-verifiable replay/holdout required."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg

from app.governance.evaluator import (
    EvaluatorError,
    load_recorded_evaluation,
    resolve_candidate_artifact,
)

ARTIFACT_TYPES = {"score_rule", "prompt", "model", "llm_profile", "quant_rule", "other"}
STATUSES = {"draft", "proposed", "approved", "rejected", "frozen"}
PASS_STATUSES = {"PASS", "pass", "passed", "PASSED"}


class GovernanceError(RuntimeError):
    pass


def _canonical_ref(ref: str | None) -> str:
    return str(ref or "").replace("\\", "/").rstrip("/").split("/")[-1].strip().lower()


def _eval_content_hash(recorded: dict[str, Any]) -> str | None:
    metrics = recorded.get("metrics") or {}
    if isinstance(metrics, str):
        metrics = json.loads(metrics)
    h = metrics.get("artifact_content_hash")
    return str(h) if h else None


def assert_eval_bound_to_proposal(
    proposal: dict[str, Any],
    recorded: dict[str, Any],
    *,
    label: str,
) -> None:
    if recorded.get("artifact_type") != proposal.get("artifact_type"):
        raise GovernanceError(
            f"{label} artifact_type {recorded.get('artifact_type')!r} "
            f"!= proposal {proposal.get('artifact_type')!r}"
        )
    if _canonical_ref(recorded.get("artifact_ref")) != _canonical_ref(proposal.get("artifact_ref")):
        raise GovernanceError(
            f"{label} artifact_ref {recorded.get('artifact_ref')!r} "
            f"!= proposal {proposal.get('artifact_ref')!r}"
        )
    if str(recorded.get("candidate_version") or "") != str(proposal.get("to_version") or ""):
        raise GovernanceError(
            f"{label} candidate_version {recorded.get('candidate_version')!r} "
            f"!= to_version {proposal.get('to_version')!r}"
        )
    if not _eval_content_hash(recorded):
        raise GovernanceError(f"{label} missing artifact_content_hash")


def assert_replay_holdout_same_candidate(replay: dict[str, Any], holdout: dict[str, Any]) -> None:
    if replay.get("artifact_type") != holdout.get("artifact_type"):
        raise GovernanceError("replay/holdout artifact_type mismatch")
    if _canonical_ref(replay.get("artifact_ref")) != _canonical_ref(holdout.get("artifact_ref")):
        raise GovernanceError("replay/holdout artifact_ref mismatch")
    if str(replay.get("candidate_version") or "") != str(holdout.get("candidate_version") or ""):
        raise GovernanceError("replay/holdout candidate_version mismatch")
    rh = _eval_content_hash(replay)
    hh = _eval_content_hash(holdout)
    if not rh or rh != hh:
        raise GovernanceError("replay/holdout content hash mismatch")


def assert_candidate_hash_current(
    proposal: dict[str, Any],
    recorded: dict[str, Any],
    *,
    repo: Any = None,
    action: str = "freeze",
) -> str:
    try:
        loaded = resolve_candidate_artifact(
            proposal["artifact_type"],
            proposal["artifact_ref"],
            proposal["to_version"],
            repo=repo,
        )
    except EvaluatorError as exc:
        raise GovernanceError(f"cannot re-hash candidate: {exc}") from exc
    expected = _eval_content_hash(recorded)
    if loaded["content_hash"] != expected:
        raise GovernanceError(f"artifact changed after evaluation; cannot {action}")
    return loaded["content_hash"]


def _require_recorded_eval(
    conn: psycopg.Connection,
    label: str,
    eval_kind: str,
    evaluation_id: str | None,
    eval_obj: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Trust only DB-recorded evaluator runs — hand-authored PASS JSON is rejected."""
    eid = evaluation_id or (eval_obj or {}).get("evaluation_id")
    if not eid:
        raise GovernanceError(f"{label} must reference a recorded evaluation_id (evaluator run required)")
    try:
        recorded = load_recorded_evaluation(conn, str(eid))
    except EvaluatorError as exc:
        raise GovernanceError(str(exc)) from exc
    if recorded["eval_kind"] != eval_kind:
        raise GovernanceError(f"{label} eval_kind must be {eval_kind}, got {recorded['eval_kind']}")
    if recorded["status"] not in PASS_STATUSES:
        raise GovernanceError(f"{label} recorded status must be PASS, got {recorded['status']!r}")
    if eval_obj and eval_obj.get("output_hash") and eval_obj["output_hash"] != recorded["output_hash"]:
        raise GovernanceError(f"{label} output_hash does not match recorded evaluation")
    return recorded


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
    replay_evaluation_id: str,
    holdout_evaluation_id: str,
) -> dict[str, Any]:
    """Attach DB-recorded evaluator runs (not hand-authored PASS JSON)."""
    replay = _require_recorded_eval(conn, "replay", "replay", replay_evaluation_id)
    holdout = _require_recorded_eval(conn, "holdout", "holdout", holdout_evaluation_id)
    with conn.cursor() as cur:
        cur.execute(
            """
            select status, artifact_type, artifact_ref, to_version
            from change_proposals where proposal_id=%s::uuid
            """,
            (proposal_id,),
        )
        row = cur.fetchone()
        if not row:
            raise GovernanceError("proposal not found")
        if row[0] not in {"draft", "proposed"}:
            raise GovernanceError(f"cannot attach evals from status={row[0]}")
        proposal = {
            "artifact_type": row[1],
            "artifact_ref": row[2],
            "to_version": row[3],
        }
        assert_eval_bound_to_proposal(proposal, replay, label="replay")
        assert_eval_bound_to_proposal(proposal, holdout, label="holdout")
        assert_replay_holdout_same_candidate(replay, holdout)
        assert_candidate_hash_current(proposal, replay, action="attach")
        assert_candidate_hash_current(proposal, holdout, action="attach")
        cur.execute(
            """
            update change_proposals set
              replay_eval=%s::jsonb,
              holdout_eval=%s::jsonb,
              replay_status=%s,
              holdout_status=%s,
              replay_evaluation_id=%s::uuid,
              holdout_evaluation_id=%s::uuid,
              updated_at=now()
            where proposal_id=%s::uuid
            """,
            (
                json.dumps(replay),
                json.dumps(holdout),
                replay["status"],
                holdout["status"],
                replay["evaluation_id"],
                holdout["evaluation_id"],
                proposal_id,
            ),
        )
    conn.commit()
    return {
        "proposal_id": proposal_id,
        "replay_status": replay["status"],
        "holdout_status": holdout["status"],
        "replay_evaluation_id": replay["evaluation_id"],
        "holdout_evaluation_id": holdout["evaluation_id"],
    }


def approve_proposal(
    conn: psycopg.Connection,
    proposal_id: str,
    *,
    replay_notes: str = "",
    holdout_notes: str = "",
    approver: str = "operator",
    replay_evaluation_id: str | None = None,
    holdout_evaluation_id: str | None = None,
    replay_eval: dict[str, Any] | None = None,
    holdout_eval: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Approve only when recorded evaluator PASS runs exist (notes/JSON alone insufficient)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            select status, approval_log, replay_eval, holdout_eval, replay_status, holdout_status,
                   replay_evaluation_id::text, holdout_evaluation_id::text,
                   artifact_type, artifact_ref, to_version
            from change_proposals where proposal_id=%s::uuid
            """,
            (proposal_id,),
        )
        row = cur.fetchone()
        if not row:
            raise GovernanceError("proposal not found")
        if row[0] != "proposed":
            raise GovernanceError(f"cannot approve from status={row[0]}")

        replay = _require_recorded_eval(
            conn, "replay", "replay", replay_evaluation_id or row[6], replay_eval
        )
        holdout = _require_recorded_eval(
            conn, "holdout", "holdout", holdout_evaluation_id or row[7], holdout_eval
        )
        proposal = {
            "artifact_type": row[8],
            "artifact_ref": row[9],
            "to_version": row[10],
        }
        assert_eval_bound_to_proposal(proposal, replay, label="replay")
        assert_eval_bound_to_proposal(proposal, holdout, label="holdout")
        assert_replay_holdout_same_candidate(replay, holdout)
        assert_candidate_hash_current(proposal, replay, action="approve")
        assert_candidate_hash_current(proposal, holdout, action="approve")

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
              replay_evaluation_id=%s::uuid,
              holdout_evaluation_id=%s::uuid,
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
                replay["evaluation_id"],
                holdout["evaluation_id"],
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
            select status, approval_log, to_version, replay_status, holdout_status,
                   artifact_type, artifact_ref, replay_evaluation_id::text, holdout_evaluation_id::text
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
        proposal = {
            "artifact_type": row[5],
            "artifact_ref": row[6],
            "to_version": row[2],
        }
        replay = _require_recorded_eval(conn, "replay", "replay", row[7])
        holdout = _require_recorded_eval(conn, "holdout", "holdout", row[8])
        assert_eval_bound_to_proposal(proposal, replay, label="replay")
        assert_eval_bound_to_proposal(proposal, holdout, label="holdout")
        assert_replay_holdout_same_candidate(replay, holdout)
        assert_candidate_hash_current(proposal, replay, action="freeze")
        assert_candidate_hash_current(proposal, holdout, action="freeze")
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
