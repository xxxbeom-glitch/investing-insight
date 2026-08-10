from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import httpx
import yaml

from app.logging_setup import get_logger

log = get_logger("fred")
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONFIG = REPO_ROOT / "config" / "fred_series.v0.1.yaml"
DEFAULT_BASE = "https://api.stlouisfed.org"


class FredUnavailableError(RuntimeError):
    """Fail-closed: missing key or provider error — no silent skip."""


def load_fred_series_config(path: Path | None = None) -> dict[str, Any]:
    raw = yaml.safe_load((path or DEFAULT_CONFIG).read_text(encoding="utf-8")) or {}
    if not raw.get("series"):
        raise FredUnavailableError("fred series config empty")
    return raw


class FredClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE,
        timeout: float = 30.0,
        min_interval_sec: float = 0.5,
        max_retries: int = 5,
    ):
        if not api_key:
            raise FredUnavailableError("FRED_API_KEY missing")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.min_interval_sec = min_interval_sec
        self.max_retries = max_retries
        self._last = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last
        if elapsed < self.min_interval_sec:
            time.sleep(self.min_interval_sec - elapsed)

    def get_observations(
        self,
        series_id: str,
        *,
        observation_start: str | None = None,
        observation_end: str | None = None,
        sort_order: str = "asc",
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": sort_order,
        }
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end

        url = f"{self.base_url}/fred/series/observations"
        last_err: Exception | None = None
        for attempt in range(self.max_retries):
            self._throttle()
            try:
                res = httpx.get(url, params=params, timeout=self.timeout)
            except httpx.HTTPError as exc:
                last_err = FredUnavailableError(f"fred request failed: {type(exc).__name__}")
                time.sleep(min(30, 2 * (attempt + 1)))
                continue
            finally:
                self._last = time.monotonic()
            if res.status_code == 429:
                time.sleep(min(60, 5 * (attempt + 1)))
                continue
            if res.status_code >= 400:
                # never include api_key in error text
                raise FredUnavailableError(f"fred HTTP {res.status_code} for series={series_id}")
            data = res.json()
            if not isinstance(data, dict) or "observations" not in data:
                raise FredUnavailableError(f"fred malformed response for series={series_id}")
            out: list[dict[str, Any]] = []
            for row in data["observations"]:
                val = row.get("value")
                if val is None or val == ".":
                    continue
                try:
                    num = float(val)
                except (TypeError, ValueError):
                    continue
                out.append({"date": row["date"], "value": num})
            log.info("fred_observations", series_id=series_id, n=len(out))
            return out
        raise FredUnavailableError(f"fred retries exhausted: {last_err}")
