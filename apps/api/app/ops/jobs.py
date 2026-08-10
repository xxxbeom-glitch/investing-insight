from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg


def start_job(
    conn: psycopg.Connection,
    *,
    job_type: str,
    stage: str,
    payload: dict[str, Any] | None = None,
    retry_count: int = 0,
) -> str:
    job_id = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into ops_jobs (
              job_id, job_type, stage, status, retry_count, payload
            ) values (%s,%s,%s,'running',%s,%s::jsonb)
            """,
            (job_id, job_type, stage, retry_count, json.dumps(payload or {})),
        )
    conn.commit()
    return job_id


def finish_job(
    conn: psycopg.Connection,
    job_id: str,
    *,
    status: str,
    stage: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    result: dict[str, Any] | None = None,
) -> None:
    if status not in ("success", "failed", "dead_letter"):
        raise ValueError(f"invalid terminal status: {status}")
    msg = (error_message or "")[:500]
    with conn.cursor() as cur:
        cur.execute(
            """
            update ops_jobs set
              status = %s,
              stage = coalesce(%s, stage),
              error_code = %s,
              error_message = %s,
              result = %s::jsonb,
              finished_at = %s
            where job_id = %s::uuid
            """,
            (
                status,
                stage,
                error_code,
                msg,
                json.dumps(result or {}),
                datetime.now(timezone.utc),
                job_id,
            ),
        )
    conn.commit()


def list_recent_jobs(conn: psycopg.Connection, *, limit: int = 20) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select job_id::text, job_type, stage, status, error_code, retry_count,
                   started_at::text, finished_at::text
            from ops_jobs
            order by started_at desc
            limit %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
    return [
        {
            "job_id": r[0],
            "job_type": r[1],
            "stage": r[2],
            "status": r[3],
            "error_code": r[4],
            "retry_count": r[5],
            "started_at": r[6],
            "finished_at": r[7],
        }
        for r in rows
    ]
