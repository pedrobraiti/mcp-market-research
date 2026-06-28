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
from ..retry import SourceUnavailable, classify_transient, unavailable_status

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
        # A keyless 429 (or timeout) typically throttles the whole IP, so BOTH legs fail. An
        # all-null CryptoMacro would read as "market cap unknown = a real zero". It is not —
        # it is "couldn't fetch". Raise so the tool surfaces an honest error envelope instead
        # (a transient failure → SourceUnavailable with a reason; a genuine error propagates raw).
        if not isinstance(glob, dict) and not isinstance(defi, dict):
            reason = classify_transient(glob) or classify_transient(defi)
            if reason is not None:
                raise SourceUnavailable(reason) from glob
            raise glob
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
        else:
            # The headline leg failed but DeFi came back: flag it so the null market cap /
            # dominance read as "unavailable", not as real zeros.
            macro.status = unavailable_status(glob)
        if isinstance(defi, dict):
            ddata = defi.get("data") or {}
            macro.defi_market_cap_usd = _dec(ddata.get("defi_market_cap"))
            macro.defi_dominance = _dec(ddata.get("defi_dominance"))
        else:
            # The DeFi leg alone failed (headline is fine). Flag it on a SCOPED field, not the
            # headline ``status`` — otherwise a consumer would discard good market-cap/dominance
            # data. So the null defi fields read as 'unavailable', not real zeros.
            macro.defi_status = unavailable_status(defi)
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
