"""CoinGecko implementation of ``CryptoMacroSource`` — keyless crypto macro & sectors.

CoinGecko's public API needs no key but rate-limits hard on shared IPs (429). The tool layer turns
a failure into an honest ``{ok:false}`` envelope; here, the two macro reads are fetched
concurrently and tolerate partial failure. Raw aggregate facts (total market cap, dominance, DeFi
share, category performance) — no regime verdict.

The JSON fetch is injected so the unit tests run fully offline.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from decimal import Decimal, InvalidOperation
from typing import Any

from ...domain.models import CryptoCategory, CryptoMacro, CryptoSectors

_GLOBAL = "https://api.coingecko.com/api/v3/global"
_GLOBAL_DEFI = "https://api.coingecko.com/api/v3/global/decentralized_finance_defi"
_CATEGORIES = "https://api.coingecko.com/api/v3/coins/categories"


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class CoinGeckoMacro:
    def __init__(
        self,
        fetch_json: Callable[[str], Awaitable[Any]] | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._timeout = timeout
        self._fetch_json = fetch_json or self._default_fetch_json

    async def _default_fetch_json(self, url: str) -> Any:
        import httpx

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_macro(self) -> CryptoMacro:
        glob, defi = await asyncio.gather(
            self._fetch_json(_GLOBAL),
            self._fetch_json(_GLOBAL_DEFI),
            return_exceptions=True,
        )
        macro = CryptoMacro()
        if isinstance(glob, dict):
            data = glob.get("data") or {}
            mcap = data.get("total_market_cap") or {}
            vol = data.get("total_volume") or {}
            dominance = data.get("market_cap_percentage") or {}
            macro.total_market_cap_usd = _dec(mcap.get("usd"))
            macro.total_volume_24h_usd = _dec(vol.get("usd"))
            macro.market_cap_change_percent_24h = _dec(
                data.get("market_cap_change_percentage_24h_usd")
            )
            macro.btc_dominance = _dec(dominance.get("btc"))
            macro.eth_dominance = _dec(dominance.get("eth"))
            macro.active_cryptocurrencies = _int(data.get("active_cryptocurrencies"))
        if isinstance(defi, dict):
            ddata = defi.get("data") or {}
            macro.defi_market_cap_usd = _dec(ddata.get("defi_market_cap"))
            macro.defi_dominance = _dec(ddata.get("defi_dominance"))
        return macro

    async def get_sectors(self) -> CryptoSectors:
        data = await self._fetch_json(_CATEGORIES)
        rows = [c for c in (data or []) if isinstance(c, dict)]
        categories = [
            CryptoCategory(
                name=c.get("name"),
                market_cap_usd=_dec(c.get("market_cap")),
                market_cap_change_24h=_dec(c.get("market_cap_change_24h")),
                volume_24h_usd=_dec(c.get("volume_24h")),
                top_3_coins=[str(x) for x in (c.get("top_3_coins_id") or [])][:3],
            )
            for c in rows
        ]
        return CryptoSectors(categories=categories[:30])
