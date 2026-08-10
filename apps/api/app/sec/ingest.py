from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg

from app.providers.massive import stable_raw_hash
from app.sec.client import SecClient
from app.sec.facts import build_ticker_cik_map, extract_fact_points


def persist_cik_map(conn: psycopg.Connection, mapping: dict[str, str]) -> int:
    updated = 0
    with conn.cursor() as cur:
        for ticker, cik in mapping.items():
            cur.execute(
                """
                update companies c
                set sec_cik = %s, updated_at = now()
                from securities s
                where s.company_id = c.company_id and s.ticker = %s
                """,
                (cik, ticker),
            )
            updated += cur.rowcount
    conn.commit()
    return updated


def persist_facts(conn: psycopg.Connection, company_id: str, fact_rows: list[dict[str, Any]], *, source_id: str) -> int:
    n = 0
    with conn.cursor() as cur:
        for row in fact_rows:
            if row.get("value") is None or not row.get("period_end"):
                continue
            fact_id = uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{company_id}:{row['metric_key']}:{row.get('period_end')}:{row.get('accn')}:{row.get('unit')}",
            )
            cur.execute(
                """
                insert into financial_facts (
                  fact_id, company_id, metric_key, value, unit, currency, fiscal_year, fiscal_quarter,
                  period_end, form_type, filed_at, published_at, source_id, source_version, accn
                ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (fact_id) do nothing
                """,
                (
                    str(fact_id),
                    company_id,
                    row["metric_key"],
                    row["value"],
                    row.get("unit"),
                    None,
                    row.get("fiscal_year"),
                    row.get("fiscal_quarter"),
                    row.get("period_end"),
                    row.get("form_type"),
                    row.get("filed_at"),
                    row.get("published_at"),
                    source_id,
                    "sec-companyfacts-v1",
                    row.get("accn"),
                ),
            )
            n += cur.rowcount
    conn.commit()
    return n


def ingest_sec_sample(db_url: str, user_agent: str, tickers: list[str]) -> dict[str, Any]:
    client = SecClient(user_agent)
    tickers_payload = client.company_tickers()
    mapping = build_ticker_cik_map(tickers_payload)
    raw_hash = stable_raw_hash({"type": "company_tickers", "n": len(mapping)})
    storage = Path(f"storage/raw/sec/company_tickers/{raw_hash}.json")
    storage.parent.mkdir(parents=True, exist_ok=True)
    # store compact size marker not full huge file every run
    storage.write_text(json.dumps({"count": len(mapping), "hash_ref": raw_hash}), encoding="utf-8")

    stats = {"tickers_mapped": 0, "facts_rows": 0, "facts_inserted": 0}
    now = datetime.now(timezone.utc)
    with psycopg.connect(db_url) as conn:
        stats["tickers_mapped"] = persist_cik_map(conn, {t: mapping[t] for t in tickers if t in mapping})
        with conn.cursor() as cur:
            for ticker in tickers:
                cik = mapping.get(ticker.upper())
                if not cik:
                    raise RuntimeError(f"CIK missing for {ticker}")
                facts = client.company_facts(cik)
                points = extract_fact_points(facts)
                stats["facts_rows"] += len(points)
                fhash = stable_raw_hash({"cik": cik, "metrics": sorted({p['metric_key'] for p in points})})
                source_id = uuid.uuid5(uuid.NAMESPACE_URL, f"sec:facts:{cik}:{fhash}")
                path = Path(f"storage/raw/sec/companyfacts/{cik}/{fhash}.json")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(facts)[:2_000_000], encoding="utf-8")  # truncate store for lab size
                cur.execute(
                    """
                    insert into sources (source_id, provider, source_type, external_id, source_uri, collected_at, raw_hash, storage_path)
                    values (%s,'sec','companyfacts',%s,%s,%s,%s,%s)
                    on conflict (provider, raw_hash) do update set collected_at=excluded.collected_at
                    returning source_id
                    """,
                    (str(source_id), cik, f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", now, fhash, str(path)),
                )
                sid = cur.fetchone()[0]
                cur.execute(
                    "select company_id from companies where sec_cik=%s limit 1",
                    (cik,),
                )
                crow = cur.fetchone()
                if not crow:
                    cur.execute(
                        """
                        select c.company_id from companies c
                        join securities s on s.company_id=c.company_id
                        where s.ticker=%s limit 1
                        """,
                        (ticker.upper(),),
                    )
                    crow = cur.fetchone()
                if not crow:
                    raise RuntimeError(f"company missing for {ticker}")
                conn.commit()
                inserted = persist_facts(conn, str(crow[0]), points, source_id=str(sid))
                stats["facts_inserted"] += inserted
    return stats
