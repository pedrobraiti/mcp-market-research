"""ApeWisdom implementation of ``RetailBuzzSource`` — keyless Reddit mention buzz.

ApeWisdom aggregates Reddit ticker mentions. It's a retail-ATTENTION signal (how much a name is
being talked about, and the change vs 24h ago) — NOT a sentiment score and skewed toward meme
names. Reported as raw counts; the agent decides what the buzz means.

The same adapter serves stocks and crypto via the ``filter_name`` (ApeWisdom's filter slug):
``all-stocks`` for equities and ``all-crypto`` for crypto. Crypto tickers come suffixed ``.X``
(e.g. ``BTC.X``); ``strip_suffix`` drops it so the symbol matches the tradable base ("BTC").

The JSON fetch is injected for offline tests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from ...domain.models import RetailBuzz, RetailBuzzItem

_URL = "https://apewisdom.io/api/v1.0/filter/{filter_name}/page/1"


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _symbol(raw: Any, strip_suffix: bool) -> str:
    text = str(raw or "").upper()
    if strip_suffix and "." in text:
        text = text.split(".", 1)[0]
    return text


def _row(entry: dict, strip_suffix: bool) -> RetailBuzzItem:
    return RetailBuzzItem(
        symbol=_symbol(entry.get("ticker"), strip_suffix),
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
        filter_name: str = "all-stocks",
        strip_suffix: bool = False,
    ) -> None:
        self._timeout = timeout
        self._fetch_json = fetch_json or self._default_fetch_json
        self._filter_name = filter_name
        self._strip_suffix = strip_suffix

    async def _default_fetch_json(self, url: str) -> dict:
        import httpx

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_buzz(self, symbol: str | None = None, limit: int = 20) -> RetailBuzz:
        data = await self._fetch_json(_URL.format(filter_name=self._filter_name))
        results = (data or {}).get("results") or []
        rows = [
            _row(entry, self._strip_suffix)
            for entry in results
            if isinstance(entry, dict) and entry.get("ticker")
        ]

        if symbol:
            wanted = _symbol(symbol.strip(), self._strip_suffix)
            match = [r for r in rows if r.symbol == wanted]
            if match:
                return RetailBuzz(symbol=wanted, items=match)
            return RetailBuzz(
                symbol=wanted,
                items=[],
                note=f"{wanted} is not in the current Reddit trending list (low/no buzz).",
            )
        return RetailBuzz(symbol=None, items=rows[: max(1, min(limit, 100))])
