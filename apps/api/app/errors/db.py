"""Error database (Post-MVP M05)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import psycopg
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
TAXONOMY_PATH = REPO_ROOT / "config" / "error_taxonomy.v0.1.yaml"


def load_error_taxonomy(path: Path | None = None) -> dict[str, Any]:
    raw = yaml.safe_load((path or TAXONOMY_PATH).read_text(encoding="utf-8")) or {}
    types = raw.get("types") or []
    if not types:
        raise ValueError("error taxonomy empty")
    return raw


def allowed_error_types(taxonomy: dict[str, Any] | None = None) -> set[str]:
    return set((taxonomy or load_error_taxonomy()).get("types") or [])


class InvalidErrorType(ValueError):
    pass


def record_error_event(
    conn: psycopg.Connection,
    *,
    error_type: str,
    summary: str,
    severity: str = "P2",
    details: dict[str, Any] | None = None,
    run_id: str | None = None,
    judgment_id: str | None = None,
    security_id: str | None = None,
    performance_eval_id: str | None = None,
) -> dict[str, Any]:
    tax = load_error_taxonomy()
    if error_type not in allowed_error_types(tax):
        raise InvalidErrorType(f"invalid error_type: {error_type}")
    if severity not in {"P0", "P1", "P2", "P3"}:
        raise ValueError(f"invalid severity: {severity}")
    if not summary.strip():
        raise ValueError("summary required")

    error_id = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into error_events (
              error_id, error_type, severity, summary, details,
              run_id, judgment_id, security_id, performance_eval_id, taxonomy_version
            ) values (%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s)
            """,
            (
                error_id,
                error_type,
                severity,
                summary.strip()[:500],
                json.dumps(details or {}),
                run_id,
                judgment_id,
                security_id,
                performance_eval_id,
                str(tax.get("version") or "error-taxonomy-v0.1"),
            ),
        )
    conn.commit()
    return {"error_id": error_id, "error_type": error_type, "severity": severity}


def list_error_events(
    conn: psycopg.Connection,
    *,
    error_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        if error_type:
            cur.execute(
                """
                select error_id::text, error_type, severity, summary, created_at::text
                from error_events
                where error_type = %s
                order by created_at desc
                limit %s
                """,
                (error_type, limit),
            )
        else:
            cur.execute(
                """
                select error_id::text, error_type, severity, summary, created_at::text
                from error_events
                order by created_at desc
                limit %s
                """,
                (limit,),
            )
        return [
            {
                "error_id": r[0],
                "error_type": r[1],
                "severity": r[2],
                "summary": r[3],
                "created_at": r[4],
            }
            for r in cur.fetchall()
        ]
