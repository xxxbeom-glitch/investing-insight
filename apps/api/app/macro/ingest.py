from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import psycopg

from app.macro.fred_client import FredClient, FredUnavailableError, load_fred_series_config
from app.providers.massive import stable_raw_hash


def ingest_fred_series(
    conn: psycopg.Connection,
    client: FredClient,
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = config or load_fred_series_config()
    version = str(cfg.get("version") or "fred-series-v0.1")
    start = str(cfg.get("default_observation_start") or "2018-01-01")
    stats = {"series": 0, "upserted": 0, "config_version": version}
    now = datetime.now(timezone.utc)

    for spec in cfg["series"]:
        series_id = spec["id"]
        role = spec.get("role")
        obs = client.get_observations(series_id, observation_start=start)
        payload = {"series_id": series_id, "n": len(obs), "start": start}
        raw_hash = stable_raw_hash(payload)
        source_id = uuid.uuid5(uuid.NAMESPACE_URL, f"fred:{series_id}:{raw_hash}")
        storage = Path(f"storage/raw/fred/{series_id}/{raw_hash}.json")
        storage.parent.mkdir(parents=True, exist_ok=True)
        storage.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        with conn.cursor() as cur:
            cur.execute(
                """
                insert into sources (source_id, provider, source_type, external_id, source_uri, collected_at, raw_hash, storage_path)
                values (%s,'fred','series_observations',%s,%s,%s,%s,%s)
                on conflict (provider, raw_hash) do update set collected_at = excluded.collected_at
                returning source_id
                """,
                (
                    str(source_id),
                    series_id,
                    f"fred://series/{series_id}",
                    now,
                    raw_hash,
                    str(storage),
                ),
            )
            sid = cur.fetchone()[0]
            for row in obs:
                oid = uuid.uuid5(uuid.NAMESPACE_URL, f"fred:{series_id}:{row['date']}")
                cur.execute(
                    """
                    insert into macro_observations (
                      observation_id, provider, series_id, role, observation_date, value,
                      collected_at, source_id, config_version
                    ) values (%s,'fred',%s,%s,%s,%s,%s,%s,%s)
                    on conflict (provider, series_id, observation_date) do update set
                      value = excluded.value,
                      role = excluded.role,
                      collected_at = excluded.collected_at,
                      source_id = excluded.source_id,
                      config_version = excluded.config_version
                    """,
                    (
                        str(oid),
                        series_id,
                        role,
                        row["date"],
                        row["value"],
                        now,
                        sid,
                        version,
                    ),
                )
                stats["upserted"] += 1
        conn.commit()
        stats["series"] += 1
    return stats


def latest_by_role(conn: psycopg.Connection) -> dict[str, dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select distinct on (role) role, series_id, observation_date::text, value
            from macro_observations
            where role is not null and value is not null
            order by role, observation_date desc
            """
        )
        out: dict[str, dict[str, Any]] = {}
        for role, series_id, d, value in cur.fetchall():
            out[role] = {"series_id": series_id, "date": d, "value": float(value)}
        return out


def require_fred_key(api_key: str) -> None:
    if not api_key:
        raise FredUnavailableError("FRED_API_KEY missing")
