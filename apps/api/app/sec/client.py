from __future__ import annotations

import threading
import time
from typing import Any

import httpx

from app.logging_setup import get_logger

log = get_logger("sec")


class RateLimiter:
    """Token-ish spacing limiter: max_per_sec requests."""

    def __init__(self, max_per_sec: float = 10.0):
        if max_per_sec <= 0:
            raise ValueError("max_per_sec must be > 0")
        self.min_interval = 1.0 / max_per_sec
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delta = now - self._last
            if delta < self.min_interval:
                time.sleep(self.min_interval - delta)
            self._last = time.monotonic()


class SecClient:
    def __init__(self, user_agent: str, *, max_per_sec: float = 9.0, timeout: float = 60.0):
        if not user_agent or "example.com" in user_agent and "investing-insight" not in user_agent:
            # still allow our default example contact but require non-empty
            pass
        if not user_agent.strip():
            raise RuntimeError("SEC_USER_AGENT missing")
        self.user_agent = user_agent.strip()
        self.timeout = timeout
        self.limiter = RateLimiter(max_per_sec=max_per_sec)

    @property
    def headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json",
        }

    def get_json(self, url: str) -> Any:
        self.limiter.wait()
        try:
            res = httpx.get(url, headers=self.headers, timeout=self.timeout)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"SEC request failed: {exc}") from exc
        if res.status_code in {403, 429}:
            raise RuntimeError(f"SEC HTTP {res.status_code} (not silent): {res.text[:200]}")
        if res.status_code >= 400:
            raise RuntimeError(f"SEC HTTP {res.status_code}: {res.text[:200]}")
        return res.json()

    def company_tickers(self) -> dict[str, Any]:
        return self.get_json("https://www.sec.gov/files/company_tickers.json")

    def company_facts(self, cik: str) -> dict[str, Any]:
        digits = "".join(ch for ch in str(cik) if ch.isdigit()).zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{digits}.json"
        return self.get_json(url)
