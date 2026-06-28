"""Coinpaprika implementation of ``CryptoAssetSource`` — keyless supply/market-cap/rank.

Coinpaprika's public API needs no key. Two reads: resolve the base asset (e.g. "BTC") to the
provider id (e.g. "btc-bitcoin") via search, then fetch that asset's ticker for supply, market
cap, rank and ATH. Aggregator data keyed by asset, independent of any single exchange — raw
facts, not a verdict on value.

The JSON fetch is injected so the unit tests run fully offline.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from ...domain.models import CryptoAssetProfile, CryptoSymbolMatch, CryptoSymbolSearch

_SEARCH_URL = "https://api.coinpaprika.com/v1/search/?q={query}&c=currencies&limit=10"
_TICKER_URL = "https://api.coinpaprika.com/v1/tickers/{coin_id}?quotes=USD"


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


def _ratio_pos(
    numerator: Decimal | None, denominator: Decimal | None, places: int
) -> Decimal | None:
    """Ratio only when the denominator is strictly positive (max_supply is null/0 for uncapped
    assets like ETH, which must yield null rather than a divide error)."""
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return (numerator / denominator).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)


def _date(raw: Any) -> date | None:
    if not raw:
        return None
    text = str(raw).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        try:
            return datetime.strptime(str(raw)[:10], "%Y-%m-%d").date()
        except ValueError:
            return None


def _pick_currency(currencies: list[dict], base: str) -> dict | None:
    """Prefer an exact symbol match (rank-ordered); fall back to the first result."""
    wanted = base.upper()
    exact = [c for c in currencies if str(c.get("symbol", "")).upper() == wanted]
    if exact:
        return min(exact, key=lambda c: _int(c.get("rank")) or 10**9)
    return currencies[0] if currencies else None


class CoinpaprikaAssets:
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

    async def get_profile(self, base: str) -> CryptoAssetProfile | None:
        query = base.strip()
        if not query:
            return None
        search = await self._fetch_json(_SEARCH_URL.format(query=query.lower()))
        currencies = (search or {}).get("currencies") or []
        chosen = _pick_currency([c for c in currencies if isinstance(c, dict)], query)
        if not chosen or not chosen.get("id"):
            return None

        coin_id = str(chosen["id"])
        ticker = await self._fetch_json(_TICKER_URL.format(coin_id=coin_id))
        if not ticker:
            return None
        usd = (ticker.get("quotes") or {}).get("USD") or {}
        circulating = _dec(ticker.get("circulating_supply"))
        total = _dec(ticker.get("total_supply"))
        max_supply = _dec(ticker.get("max_supply"))
        future_overhang = max_supply - circulating if max_supply and circulating else None
        return CryptoAssetProfile(
            base=str(ticker.get("symbol", query)).upper(),
            name=ticker.get("name"),
            source_id=coin_id,
            rank=_int(ticker.get("rank")),
            price_usd=_dec(usd.get("price")),
            market_cap_usd=_dec(usd.get("market_cap")),
            volume_24h_usd=_dec(usd.get("volume_24h")),
            circulating_supply=circulating,
            total_supply=total,
            max_supply=max_supply,
            ath_price_usd=_dec(usd.get("ath_price")),
            ath_date=_date(usd.get("ath_date")),
            percent_from_ath=_dec(usd.get("percent_from_price_ath")),
            float_ratio=_ratio_pos(circulating, total, 4),
            issuance_progress=_ratio_pos(circulating, max_supply, 4),
            future_dilution=_ratio_pos(future_overhang, circulating, 4),
        )

    async def search(self, query: str, limit: int = 10) -> CryptoSymbolSearch:
        text = query.strip()
        if not text:
            return CryptoSymbolSearch(query=query, matches=[])
        search = await self._fetch_json(_SEARCH_URL.format(query=text.lower()))
        currencies = [c for c in ((search or {}).get("currencies") or []) if isinstance(c, dict)]
        currencies.sort(key=lambda c: _int(c.get("rank")) or 10**9)
        matches = [
            CryptoSymbolMatch(
                base=str(c.get("symbol", "")).upper(),
                name=c.get("name"),
                source_id=c.get("id"),
                rank=_int(c.get("rank")),
            )
            for c in currencies[: max(1, min(int(limit), 50))]
        ]
        return CryptoSymbolSearch(query=query, matches=matches)
