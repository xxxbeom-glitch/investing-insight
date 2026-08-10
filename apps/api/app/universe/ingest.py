from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import psycopg

from app.providers.massive import MassiveClient, stable_raw_hash
from app.universe.classify import RULE_VERSION, UNIVERSE_NAME
from app.universe.identity import build_identity


def persist_tickers(
    conn: psycopg.Connection,
    rows: Iterable[dict[str, Any]],
    *,
    provider: str = "massive",
    write_raw_files: bool = True,
) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "seen": 0,
        "included": 0,
        "excluded": 0,
        "companies": 0,
        "securities": 0,
        "nyse": 0,
        "nasdaq": 0,
        "included_common": 0,
        "included_adr": 0,
        "exclusions_by_reason": {},
        "missing_cik": 0,
    }
    with conn.cursor() as cur:
        for row in rows:
            now = datetime.now(timezone.utc)
            stats["seen"] += 1
            identity = build_identity(row)
            raw_hash = stable_raw_hash(row)
            source_id = uuid.uuid5(uuid.NAMESPACE_URL, f"{provider}:{raw_hash}")
            storage_path = f"storage/raw/{provider}/tickers/{raw_hash}.json"
            if write_raw_files:
                Path(storage_path).parent.mkdir(parents=True, exist_ok=True)
                Path(storage_path).write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
            else:
                storage_path = f"db-only://{provider}/tickers/{raw_hash}"

            cur.execute(
                """
                insert into sources (source_id, provider, source_type, external_id, source_uri, collected_at, raw_hash, storage_path)
                values (%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (provider, raw_hash) do update set collected_at = excluded.collected_at
                returning source_id
                """,
                (
                    str(source_id),
                    provider,
                    "ticker_reference",
                    identity.ticker,
                    f"massive://ticker/{identity.ticker}",
                    now,
                    raw_hash,
                    storage_path,
                ),
            )
            source_row = cur.fetchone()
            sid = source_row[0] if source_row else str(source_id)

            cur.execute(
                """
                insert into companies (company_id, legal_name, country_of_incorporation, sec_cik, active_status)
                values (%s,%s,%s,%s,%s)
                on conflict (company_id) do update set
                  legal_name = excluded.legal_name,
                  sec_cik = coalesce(excluded.sec_cik, companies.sec_cik),
                  updated_at = now()
                """,
                (
                    str(identity.company_id),
                    identity.legal_name,
                    "US" if str(row.get("locale") or "").lower() == "us" else None,
                    identity.sec_cik,
                    bool(row.get("active", True)),
                ),
            )
            stats["companies"] += 1

            cur.execute(
                """
                insert into securities (
                  security_id, company_id, ticker, exchange, security_type, is_adr,
                  provider_ticker, composite_figi, share_class_figi, locale, currency_name, active_status
                ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (exchange, ticker) do update set
                  company_id = excluded.company_id,
                  security_type = excluded.security_type,
                  is_adr = excluded.is_adr,
                  composite_figi = coalesce(excluded.composite_figi, securities.composite_figi),
                  share_class_figi = coalesce(excluded.share_class_figi, securities.share_class_figi),
                  active_status = excluded.active_status,
                  updated_at = now()
                returning security_id
                """,
                (
                    str(identity.security_id),
                    str(identity.company_id),
                    identity.ticker,
                    identity.exchange or "UNKNOWN",
                    identity.security_type,
                    identity.is_adr,
                    identity.ticker,
                    row.get("composite_figi"),
                    row.get("share_class_figi"),
                    row.get("locale"),
                    row.get("currency_name"),
                    bool(row.get("active", True)),
                ),
            )
            sec_id = cur.fetchone()[0]
            stats["securities"] += 1

            cls = identity.classification
            if identity.exchange == "XNYS":
                stats["nyse"] += 1
            elif identity.exchange == "XNAS":
                stats["nasdaq"] += 1
            if cls.included:
                stats["included"] += 1
                if identity.is_adr:
                    stats["included_adr"] += 1
                else:
                    stats["included_common"] += 1
            else:
                stats["excluded"] += 1
                reason = cls.exclusion_reason or "unknown"
                reasons = stats["exclusions_by_reason"]
                reasons[reason] = int(reasons.get(reason, 0)) + 1
            if not identity.sec_cik:
                stats["missing_cik"] += 1

            cur.execute(
                """
                insert into universe_memberships (
                  security_id, universe_name, included, inclusion_reason, exclusion_reason,
                  evaluated_at, rule_version, source_id
                ) values (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    str(sec_id),
                    UNIVERSE_NAME,
                    cls.included,
                    cls.inclusion_reason,
                    cls.exclusion_reason,
                    now,
                    RULE_VERSION,
                    sid,
                ),
            )
    conn.commit()
    return stats


def ingest_from_massive(
    db_url: str,
    api_key: str,
    *,
    tickers: list[str] | None = None,
    max_pages: int | None = 1,
    write_raw_files: bool = True,
    page_commit_size: int = 1000,
    exchanges: list[str] | None = None,
) -> dict[str, Any]:
    """Stream Massive pages into DB to avoid loading the full registry in memory."""
    client = MassiveClient(api_key)
    merged: dict[str, Any] = {
        "seen": 0,
        "included": 0,
        "excluded": 0,
        "companies": 0,
        "securities": 0,
        "nyse": 0,
        "nasdaq": 0,
        "included_common": 0,
        "included_adr": 0,
        "exclusions_by_reason": {},
        "missing_cik": 0,
        "pages": 0,
    }

    def _merge(part: dict[str, Any]) -> None:
        for k, v in part.items():
            if k == "exclusions_by_reason":
                for reason, n in v.items():
                    merged["exclusions_by_reason"][reason] = int(
                        merged["exclusions_by_reason"].get(reason, 0)
                    ) + int(n)
            elif isinstance(v, int):
                merged[k] = int(merged.get(k, 0)) + v

    if tickers:
        rows: list[dict[str, Any]] = []
        for t in tickers:
            detail = client.get_security_details(t)
            if detail is None:
                raise RuntimeError(f"massive ticker not found: {t}")
            rows.append(detail)
        with psycopg.connect(db_url) as conn:
            return persist_tickers(conn, rows, write_raw_files=write_raw_files)

    exchange_list = exchanges or [None]
    with psycopg.connect(db_url) as conn:
        for exchange in exchange_list:
            batch: list[dict[str, Any]] = []
            for row in client.list_securities(max_pages=max_pages, exchange=exchange):
                batch.append(row)
                if len(batch) >= page_commit_size:
                    merged["pages"] = int(merged.get("pages", 0)) + 1
                    part = persist_tickers(conn, batch, write_raw_files=write_raw_files)
                    _merge(part)
                    print(
                        f"exchange={exchange} page={merged['pages']} seen={merged['seen']} included={merged['included']}",
                        flush=True,
                    )
                    batch = []
            if batch:
                merged["pages"] = int(merged.get("pages", 0)) + 1
                part = persist_tickers(conn, batch, write_raw_files=write_raw_files)
                _merge(part)
                print(
                    f"exchange={exchange} page={merged['pages']} seen={merged['seen']} included={merged['included']}",
                    flush=True,
                )
    return merged
