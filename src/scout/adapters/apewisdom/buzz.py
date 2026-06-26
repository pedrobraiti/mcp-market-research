"""ApeWisdom implementation of ``RetailBuzzSource`` — keyless Reddit mention buzz.

ApeWisdom aggregates Reddit (WallStreetBets / r/stocks) ticker mentions. It's a retail-ATTENTION
signal (how much a name is being talked about, and the change vs 24h ago) — NOT a sentiment score
and skewed toward meme names. Reported as raw counts; the agent decides what the buzz means.

The JSON fetch is injected for offline tests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from ...domain.models import RetailBuzz, RetailBuzzItem

_URL = "https://apewisdom.io/api/v1.0/filter/all-stocks/page/1"


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _row(entry: dict) -> RetailBuzzItem:
    return RetailBuzzItem(
        symbol=str(entry.get("ticker", "")).upper(),
        name=entry.get("name"),
        rank=_int(entry.get("rank")),
        rank_24h_ago=_int(entry.get("rank_24h_ago")),
        mentions=_int(entry.get("mentions")),
        mentions_24h_ago=_int(entry.get("mentions_24h_ago")),
        upvotes=_int(entry.get("upvotes")),
    )


class ApeWisdomBuzz:
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

    async def get_buzz(self, symbol: str | None = None, limit: int = 20) -> RetailBuzz:
        data = await self._fetch_json(_URL)
        results = (data or {}).get("results") or []
        rows = [_row(entry) for entry in results if isinstance(entry, dict) and entry.get("ticker")]

        if symbol:
            wanted = symbol.strip().upper()
            match = [r for r in rows if r.symbol == wanted]
            if match:
                return RetailBuzz(symbol=wanted, items=match)
            return RetailBuzz(
                symbol=wanted,
                items=[],
                note=f"{wanted} is not in the current Reddit trending list (low/no buzz).",
            )
        return RetailBuzz(symbol=None, items=rows[: max(1, min(limit, 100))])
