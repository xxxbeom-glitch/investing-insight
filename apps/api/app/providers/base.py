from __future__ import annotations

from typing import Any, Iterator, Protocol


class MarketDataProvider(Protocol):
    def list_securities(
        self,
        *,
        market: str = "stocks",
        active: bool = True,
        limit: int = 1000,
        ticker: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield provider-native ticker dicts."""

    def get_security_details(self, ticker: str) -> dict[str, Any] | None:
        ...
