"""Price-history fallback decorator.

Wraps a primary ``MarketDataSource`` and, for ``get_price_history`` only, falls back to a second
source when the primary fails or returns nothing. Everything else is delegated to the primary
unchanged. This is what makes the scraper-based yfinance resilient: a transient failure or empty
result transparently retries against stooq.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from ..domain.models import PriceHistory


class PriceFallbackMarketData:
    def __init__(self, primary: Any, fallback: Any) -> None:
        self._primary = primary
        self._fallback = fallback

    def __getattr__(self, name: str) -> Any:
        # Everything not defined here (get_snapshot, get_news, ...) goes straight to the primary.
        return getattr(self._primary, name)

    async def get_price_history(
        self, symbol: str, range: str = "6mo", interval: str = "1d", as_of: date | None = None
    ) -> PriceHistory | None:
        primary_result: PriceHistory | None = None
        try:
            primary_result = await self._primary.get_price_history(symbol, range, interval, as_of)
        except Exception:  # noqa: BLE001 — fall back rather than propagate a primary failure
            primary_result = None
        if primary_result is not None and primary_result.bars:
            return primary_result
        try:
            fallback_result = await self._fallback.get_price_history(symbol, range, interval, as_of)
        except Exception:  # noqa: BLE001
            return primary_result
        return fallback_result if fallback_result is not None else primary_result
