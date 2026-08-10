from __future__ import annotations

import hashlib
import json
from typing import Any, Iterator

import httpx

from app.logging_setup import get_logger

log = get_logger("massive")

DEFAULT_BASE = "https://api.massive.com"


class MassiveClient:
    """Massive (Polygon-compatible) reference data adapter."""

    def __init__(self, api_key: str, *, base_url: str = DEFAULT_BASE, timeout: float = 30.0):
        if not api_key:
            raise RuntimeError("MASSIVE_API_KEY missing")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        q = dict(params or {})
        q["apiKey"] = self.api_key
        try:
            res = httpx.get(url, params=q, timeout=self.timeout)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"massive request failed: {exc}") from exc
        if res.status_code >= 400:
            raise RuntimeError(f"massive HTTP {res.status_code}: {res.text[:200]}")
        data = res.json()
        if not isinstance(data, dict):
            raise RuntimeError("massive response is not an object")
        return data

    def list_securities(
        self,
        *,
        market: str = "stocks",
        active: bool = True,
        limit: int = 1000,
        ticker: str | None = None,
        max_pages: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        params: dict[str, Any] = {
            "market": market,
            "active": str(active).lower(),
            "limit": min(limit, 1000),
            "order": "asc",
            "sort": "ticker",
        }
        if ticker:
            params["ticker"] = ticker

        url: str | None = f"{self.base_url}/v3/reference/tickers"
        pages = 0
        first = True
        while url:
            data = self._request(url, params if first else None)
            first = False
            for row in data.get("results") or []:
                if isinstance(row, dict):
                    yield row
            pages += 1
            if max_pages is not None and pages >= max_pages:
                break
            url = data.get("next_url")

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
