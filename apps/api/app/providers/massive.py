from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Iterator

import httpx

from app.logging_setup import get_logger

log = get_logger("massive")

DEFAULT_BASE = "https://api.massive.com"


class MassiveClient:
    """Massive (Polygon-compatible) reference data adapter."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE,
        timeout: float = 60.0,
        min_interval_sec: float = 12.0,
        max_retries: int = 8,
    ):
        if not api_key:
            raise RuntimeError("MASSIVE_API_KEY missing")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.min_interval_sec = min_interval_sec
        self.max_retries = max_retries
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_interval_sec:
            time.sleep(self.min_interval_sec - elapsed)

    def _request(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        q = dict(params or {})
        q["apiKey"] = self.api_key
        last_err: Exception | None = None
        for attempt in range(self.max_retries):
            self._throttle()
            try:
                res = httpx.get(url, params=q, timeout=self.timeout)
            except httpx.HTTPError as exc:
                last_err = RuntimeError(f"massive request failed: {exc}")
                time.sleep(min(60, 5 * (attempt + 1)))
                continue
            finally:
                self._last_request_at = time.monotonic()
            if res.status_code == 429:
                wait = min(120, 15 * (attempt + 1))
                log.warning("massive_rate_limited", attempt=attempt, wait=wait)
                time.sleep(wait)
                continue
            if res.status_code >= 400:
                raise RuntimeError(f"massive HTTP {res.status_code}: {res.text[:200]}")
            data = res.json()
            if not isinstance(data, dict):
                raise RuntimeError("massive response is not an object")
            return data
        raise RuntimeError(f"massive retries exhausted: {last_err}")

    def list_securities(
        self,
        *,
        market: str = "stocks",
        active: bool = True,
        limit: int = 1000,
        ticker: str | None = None,
        exchange: str | None = None,
        max_pages: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Paginate tickers. Prefer ticker-cursor when exchange is set (next_url may drop filters)."""
        pages = 0
        last_ticker: str | None = None
        while True:
            params: dict[str, Any] = {
                "market": market,
                "active": str(active).lower(),
                "limit": min(limit, 1000),
                "order": "asc",
                "sort": "ticker",
            }
            if ticker:
                params["ticker"] = ticker
            if exchange:
                params["exchange"] = exchange
            if last_ticker:
                # exclusive lower bound to continue after previous page
                params["ticker.gt"] = last_ticker
            data = self._request(f"{self.base_url}/v3/reference/tickers", params)
            results = [r for r in (data.get("results") or []) if isinstance(r, dict)]
            if not results:
                break
            for row in results:
                # hard filter: if exchange requested, skip mismatches (API drift)
                if exchange:
                    pe = str(row.get("primary_exchange") or "").upper()
                    if pe != exchange.upper():
                        continue
                yield row
            pages += 1
            last_ticker = str(results[-1].get("ticker") or "")
            if not last_ticker:
                break
            if max_pages is not None and pages >= max_pages:
                break
            if ticker:
                break
            if len(results) < min(limit, 1000):
                break
    def get_security_details(self, ticker: str) -> dict[str, Any] | None:
        data = self._request(
            f"{self.base_url}/v3/reference/tickers",
            {"ticker": ticker, "market": "stocks", "limit": 1},
        )
        results = data.get("results") or []
        return results[0] if results else None

    def get_daily_aggs(self, ticker: str, start: str, end: str, *, adjusted: bool = True) -> dict[str, Any]:
        path = f"/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        return self._request(
            f"{self.base_url}{path}",
            {"adjusted": str(adjusted).lower(), "sort": "asc", "limit": 50000},
        )


def stable_raw_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
