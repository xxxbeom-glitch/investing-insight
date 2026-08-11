from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg

from app.universe.classify import RULE_VERSION as UNIVERSE_RULE_VERSION

QUANT_RULE_VERSION = "quant-rules-v0.1"
_SCHEMA_PATH = (
    Path(__file__).resolve().parents[4] / "packages" / "schemas" / "snapshot_manifest.schema.json"
)


def _hash_manifest(manifest: dict[str, Any]) -> str:
    blob = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def validate_snapshot_manifest(manifest: dict[str, Any]) -> None:
    """Fail-closed check against snapshot_manifest.schema.json (no jsonschema dep)."""
    raw = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    required = raw.get("required", [])
    props = set(raw.get("properties", {}).keys())
    missing = [k for k in required if k not in manifest]
    if missing:
        raise ValueError(f"snapshot manifest missing keys: {missing}")
    if raw.get("additionalProperties") is False:
        extra = [k for k in manifest if k not in props]
        if extra:
            raise ValueError(f"snapshot manifest extra keys: {extra}")
    for k in ("snapshot_id", "run_id", "cutoff_at", "content_hash"):
        if not isinstance(manifest.get(k), str) or not manifest[k]:
            raise ValueError(f"snapshot manifest invalid {k}")
    if not isinstance(manifest.get("source_versions"), list):
        raise ValueError("source_versions must be list")
    if not isinstance(manifest.get("config_versions"), dict):
        raise ValueError("config_versions must be object")


def create_snapshot(
    conn: psycopg.Connection,
    *,
    cutoff_at: datetime,
    code_commit_hash: str | None = None,
    llm_profile_version: str = "llm-profile-v0.1",
    security_ids: list[str] | None = None,
) -> dict[str, Any]:
    if cutoff_at.tzinfo is None:
        cutoff_at = cutoff_at.replace(tzinfo=timezone.utc)
    run_id = uuid.uuid4()
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into research_runs (
              run_id, status, cutoff_at, quant_rule_version, llm_profile_version,
              code_commit_hash, universe_rule_version
            ) values (%s,'snapshot_building',%s,%s,%s,%s,%s)
            """,
            (
                str(run_id),
                cutoff_at,
                QUANT_RULE_VERSION,
                llm_profile_version,
                code_commit_hash,
                UNIVERSE_RULE_VERSION,
            ),
        )
        # latest membership as of cutoff (eligible_at = evaluated_at <= cutoff)
        if security_ids:
            cur.execute(
                """
                select distinct on (s.security_id)
                  s.security_id::text, s.ticker, s.exchange, um.included, um.exclusion_reason, um.evaluated_at
                from securities s
                join universe_memberships um on um.security_id = s.security_id
                where um.evaluated_at <= %s
                  and s.security_id = any(%s::uuid[])
                order by s.security_id, um.evaluated_at desc, um.included asc
                """,
                (cutoff_at, security_ids),
            )
        else:
            cur.execute(
                """
                select distinct on (s.security_id)
                  s.security_id::text, s.ticker, s.exchange, um.included, um.exclusion_reason, um.evaluated_at
                from securities s
                join universe_memberships um on um.security_id = s.security_id
                where um.evaluated_at <= %s
                order by s.security_id, um.evaluated_at desc, um.included asc
                """,
                (cutoff_at,),
            )
        memberships = cur.fetchall()
        items: list[dict[str, Any]] = []
        for sid, ticker, exchange, included, excl, evaluated_at in memberships:
            if evaluated_at and evaluated_at > cutoff_at:
                raise RuntimeError("future membership leaked into snapshot")
            payload = {
                "ticker": ticker,
                "exchange": exchange,
                "included": included,
                "exclusion_reason": excl,
                "evaluated_at": evaluated_at.isoformat() if evaluated_at else None,
            }
            items.append({"item_type": "universe_membership", "item_ref": sid, "payload": payload})

        cutoff_date = cutoff_at.date()
        if security_ids:
            cur.execute(
                """
                select security_id::text, trading_date::text, open, high, low, close, volume
                from daily_prices
                where trading_date <= %s and security_id = any(%s::uuid[])
                """,
                (cutoff_date, security_ids),
            )
        else:
            cur.execute(
                """
                select security_id::text, trading_date::text, open, high, low, close, volume
                from daily_prices
                where trading_date <= %s
                """,
                (cutoff_date,),
            )
        for sid, td, o, h, l, c, v in cur.fetchall():
            items.append(
                {
                    "item_type": "daily_price",
                    "item_ref": f"{sid}:{td}",
                    "payload": {
                        "security_id": sid,
                        "trading_date": td,
                        "open": float(o),
                        "high": float(h),
                        "low": float(l),
                        "close": float(c),
                        "volume": float(v),
                    },
                }
            )

        # facts known by cutoff (published/filed); period_end alone is not eligibility
        if security_ids:
            cur.execute(
                """
                select fact_id::text, company_id::text, metric_key, value::text, period_end::text,
                       published_at::text, filed_at::text, source_id::text, source_version
                from financial_facts f
                where coalesce(published_at, filed_at) is not null
                  and coalesce(published_at, filed_at) <= %s
                  and exists (
                    select 1 from securities s
                    where s.company_id=f.company_id and s.security_id = any(%s::uuid[])
                  )
                """,
                (cutoff_date, security_ids),
            )
        else:
            cur.execute(
                """
                select fact_id::text, company_id::text, metric_key, value::text, period_end::text,
                       published_at::text, filed_at::text, source_id::text, source_version
                from financial_facts
                where coalesce(published_at, filed_at) is not null
                  and coalesce(published_at, filed_at) <= %s
                """,
                (cutoff_date,),
            )
        source_ids: set[str] = set()
        for fact_id, company_id, metric, value, pe, pub, filed, source_id, source_version in cur.fetchall():
            if source_id:
                source_ids.add(source_id)
            items.append(
                {
                    "item_type": "financial_fact",
                    "item_ref": fact_id,
                    "payload": {
                        "company_id": company_id,
                        "metric_key": metric,
                        "value": value,
                        "period_end": pe,
                        "published_at": pub,
                        "filed_at": filed,
                        "source_id": source_id,
                        "source_version": source_version,
                    },
                }
            )

        source_versions: list[dict[str, Any]] = []
        if source_ids:
            cur.execute(
                """
                select source_id::text, provider, source_type, raw_hash, published_at::text, collected_at::text
                from sources
                where source_id = any(%s::uuid[])
                order by provider, source_id
                """,
                (list(source_ids),),
            )
            for sid, provider, stype, raw_hash, pub, collected in cur.fetchall():
                source_versions.append(
                    {
                        "source_id": sid,
                        "provider": provider,
                        "source_type": stype,
                        "raw_hash": raw_hash,
                        "published_at": pub,
                        "collected_at": collected,
                    }
                )

        sorted_items = sorted(items, key=lambda x: (x["item_type"], x["item_ref"]))
        config_versions = {
            "universe_rule_version": UNIVERSE_RULE_VERSION,
            "quant_rule_version": QUANT_RULE_VERSION,
            "llm_profile_version": llm_profile_version,
            "code_commit_hash": code_commit_hash,
        }
        hash_payload = {
            "cutoff_at": cutoff_at.isoformat(),
            "config_versions": config_versions,
            "source_versions": source_versions,
            "items": sorted_items,
        }
        content_hash = _hash_manifest(hash_payload)
        snapshot_id = uuid.uuid5(uuid.NAMESPACE_URL, f"cutoff:{cutoff_at.isoformat()}:{content_hash}")

        cur.execute(
            "select snapshot_id::text, run_id::text from snapshots where content_hash=%s limit 1",
            (content_hash,),
        )
        existing = cur.fetchone()
        if existing:
            cur.execute("delete from research_runs where run_id=%s", (str(run_id),))
            conn.commit()
            counts = {
                "universe_membership": sum(1 for i in items if i["item_type"] == "universe_membership"),
                "daily_price": sum(1 for i in items if i["item_type"] == "daily_price"),
                "financial_fact": sum(1 for i in items if i["item_type"] == "financial_fact"),
            }
            return {
                "run_id": existing[1],
                "snapshot_id": existing[0],
                "content_hash": content_hash,
                "counts": counts,
                "reused": True,
            }

        public_manifest = {
            "snapshot_id": str(snapshot_id),
            "run_id": str(run_id),
            "cutoff_at": cutoff_at.isoformat(),
            "content_hash": content_hash,
            "source_versions": source_versions,
            "config_versions": config_versions,
        }
        validate_snapshot_manifest(public_manifest)

        cur.execute(
            """
            insert into snapshots (snapshot_id, run_id, cutoff_at, content_hash, manifest)
            values (%s,%s,%s,%s,%s::jsonb)
            """,
            (str(snapshot_id), str(run_id), cutoff_at, content_hash, json.dumps(public_manifest)),
        )
        for item in sorted_items:
            cur.execute(
                """
                insert into snapshot_items (snapshot_id, item_type, item_ref, payload)
                values (%s,%s,%s,%s::jsonb)
                """,
                (str(snapshot_id), item["item_type"], item["item_ref"], json.dumps(item["payload"])),
            )
        # Seal after items inserted — blocks further snapshot_items mutation (ER-P0-01)
        cur.execute(
            "update snapshots set sealed = true where snapshot_id = %s",
            (str(snapshot_id),),
        )
        cur.execute("update research_runs set status='snapshot_ready' where run_id=%s", (str(run_id),))
    conn.commit()
    return {
        "run_id": str(run_id),
        "snapshot_id": str(snapshot_id),
        "content_hash": content_hash,
        "counts": {
            "universe_membership": sum(1 for i in items if i["item_type"] == "universe_membership"),
            "daily_price": sum(1 for i in items if i["item_type"] == "daily_price"),
            "financial_fact": sum(1 for i in items if i["item_type"] == "financial_fact"),
        },
        "manifest": public_manifest,
        "sealed": True,
    }
