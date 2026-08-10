from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg

from app.market.daily import MarketDataError, fetch_daily_bars, normalize_bar
from app.providers.massive import MassiveClient, stable_raw_hash


def persist_daily_bars(
    conn: psycopg.Connection,
    *,
    security_id: str,
    ticker: str,
    raw_bars: list[dict[str, Any]],
    provider: str = "massive",
) -> dict[str, int]:
    stats = {"raw": len(raw_bars), "upserted": 0, "rejected": 0}
    now = datetime.now(timezone.utc)
    payload = {"ticker": ticker, "bars": raw_bars}
    raw_hash = stable_raw_hash(payload)
    source_id = uuid.uuid5(uuid.NAMESPACE_URL, f"{provider}:daily:{ticker}:{raw_hash}")
    storage_path = f"storage/raw/{provider}/daily/{ticker}/{raw_hash}.json"
    Path(storage_path).parent.mkdir(parents=True, exist_ok=True)
    Path(storage_path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with conn.cursor() as cur:
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
                "daily_aggs",
                ticker,
                f"massive://aggs/day/{ticker}",
                now,
                raw_hash,
                storage_path,
            ),
        )
        sid = cur.fetchone()[0]
        for raw in raw_bars:
            try:
                bar = normalize_bar(raw)
            except MarketDataError:
                stats["rejected"] += 1
                continue
            cur.execute(
                """
                insert into daily_prices (
                  security_id, trading_date, open, high, low, close, adjusted_close, volume,
                  currency, source_id, source_version, collected_at
                ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (security_id, trading_date) do update set
                  open = excluded.open,
                  high = excluded.high,
                  low = excluded.low,
                  close = excluded.close,
                  adjusted_close = excluded.adjusted_close,
                  volume = excluded.volume,
                  source_id = excluded.source_id,
                  collected_at = excluded.collected_at
                """,
                (
                    security_id,
                    bar["trading_date"],
                    bar["open"],
                    bar["high"],
                    bar["low"],
                    bar["close"],
                    bar["adjusted_close"],
                    bar["volume"],
                    "USD",
                    sid,
                    "aggs-v2-1d",
                    now,
                ),
            )
            stats["upserted"] += 1
    conn.commit()
    return stats


def ingest_ticker_daily(
    db_url: str,
    api_key: str,
    ticker: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    client = MassiveClient(api_key)
    raw = fetch_daily_bars(client, ticker, start, end)
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select security_id from securities where ticker = %s order by updated_at desc nulls last limit 1",
                (ticker.upper(),),
            )
            row = cur.fetchone()
            if not row:
                raise MarketDataError(f"security not found for ticker {ticker}")
            security_id = str(row[0])
        stats = persist_daily_bars(conn, security_id=security_id, ticker=ticker.upper(), raw_bars=raw)
    stats["ticker"] = ticker.upper()
    stats["fetched"] = len(raw)
    return stats
