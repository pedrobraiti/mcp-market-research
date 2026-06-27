"""alternative.me implementation of ``CryptoSentimentSource`` — the Crypto Fear & Greed Index.

A keyless, single-endpoint, market-wide sentiment gauge (0-100) with daily history. The
de-facto industry standard since 2018. Raw index + classification; the agent reads the level,
Scout draws no buy/sell conclusion.

The JSON fetch is injected so the unit tests run fully offline.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime
from typing import Any

from ...domain.models import CryptoFearGreed, FearGreedPoint

_URL = "https://api.alternative.me/fng/?limit={limit}&format=json"


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _date(raw: Any) -> date | None:
    try:
        return datetime.fromtimestamp(int(raw), tz=UTC).date()
    except (TypeError, ValueError, OverflowError):
        return None


def _point(entry: dict) -> FearGreedPoint:
    return FearGreedPoint(
        value=_int(entry.get("value")),
        classification=entry.get("value_classification"),
        observation_date=_date(entry.get("timestamp")),
    )


class AlternativeFearGreed:
    def __init__(
        self,
        fetch_json: Callable[[str], Awaitable[dict]] | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._timeout = timeout
        self._fetch_json = fetch_json or self._default_fetch_json

    async def _default_fetch_json(self, url: str) -> dict:
        import httpx

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_fear_greed(self, days: int = 30) -> CryptoFearGreed:
        limit = max(1, min(int(days), 1000))
        data = await self._fetch_json(_URL.format(limit=limit))
        rows = [e for e in ((data or {}).get("data") or []) if isinstance(e, dict)]
        history = [_point(e) for e in rows]
        current = history[0] if history else FearGreedPoint()
        return CryptoFearGreed(
            value=current.value,
            classification=current.classification,
            observation_date=current.observation_date,
            history=history,
        )
