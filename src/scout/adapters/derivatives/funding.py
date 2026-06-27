"""Perp funding rate & open interest across exchanges — keyless public derivatives data.

The execution side is spot-only, so this is purely positioning/sentiment CONTEXT (funding sign &
size, OI level) — never executed. Aggregates Binance USDⓈ-M futures, Bybit v5 and OKX v5 public
endpoints (all keyless for market data). A venue that fails is dropped; the call still returns.

The JSON fetch is injected so the unit tests run fully offline.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from ...domain.models import CryptoDerivatives, DerivativesVenue

_BINANCE = "https://fapi.binance.com/fapi/v1"
_BYBIT = "https://api.bybit.com/v5"
_OKX = "https://www.okx.com/api/v5"


def _dec(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _ms_to_dt(ms: Any) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=UTC)
    except (TypeError, ValueError, OverflowError):
        return None


class DerivativesAggregator:
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

    async def get_derivatives(self, base: str) -> CryptoDerivatives:
        token = base.strip().upper().split("/")[0]
        results = await asyncio.gather(
            self._binance(token),
            self._bybit(token),
            self._okx(token),
            return_exceptions=True,
        )
        venues = [v for v in results if isinstance(v, DerivativesVenue)]
        note = None if venues else "No derivatives venue returned data for this asset."
        return CryptoDerivatives(base=token, venues=venues, note=note)

    async def _binance(self, base: str) -> DerivativesVenue:
        symbol = f"{base}USDT"
        premium, oi = await asyncio.gather(
            self._fetch_json(f"{_BINANCE}/premiumIndex?symbol={symbol}"),
            self._fetch_json(f"{_BINANCE}/openInterest?symbol={symbol}"),
        )
        mark = _dec((premium or {}).get("markPrice"))
        oi_base = _dec((oi or {}).get("openInterest"))
        oi_value = oi_base * mark if oi_base is not None and mark is not None else None
        return DerivativesVenue(
            exchange="binance",
            symbol=symbol,
            funding_rate=_dec((premium or {}).get("lastFundingRate")),
            next_funding_time=_ms_to_dt((premium or {}).get("nextFundingTime")),
            mark_price=mark,
            open_interest=oi_base,
            open_interest_value=oi_value,
        )

    async def _bybit(self, base: str) -> DerivativesVenue:
        symbol = f"{base}USDT"
        data = await self._fetch_json(
            f"{_BYBIT}/market/tickers?category=linear&symbol={symbol}"
        )
        rows = ((data or {}).get("result") or {}).get("list") or []
        if not rows:
            raise ValueError("bybit: no ticker")
        row = rows[0]
        return DerivativesVenue(
            exchange="bybit",
            symbol=symbol,
            funding_rate=_dec(row.get("fundingRate")),
            next_funding_time=_ms_to_dt(row.get("nextFundingTime")),
            mark_price=_dec(row.get("markPrice")),
            open_interest=_dec(row.get("openInterest")),
            open_interest_value=_dec(row.get("openInterestValue")),
        )

    async def _okx(self, base: str) -> DerivativesVenue:
        inst = f"{base}-USDT-SWAP"
        funding, oi = await asyncio.gather(
            self._fetch_json(f"{_OKX}/public/funding-rate?instId={inst}"),
            self._fetch_json(f"{_OKX}/public/open-interest?instType=SWAP&instId={inst}"),
        )
        frow = ((funding or {}).get("data") or [{}])[0]
        orow = ((oi or {}).get("data") or [{}])[0]
        return DerivativesVenue(
            exchange="okx",
            symbol=inst,
            funding_rate=_dec(frow.get("fundingRate")),
            next_funding_time=_ms_to_dt(frow.get("nextFundingTime")),
            mark_price=None,
            open_interest=_dec(orow.get("oiCcy")),
            open_interest_value=_dec(orow.get("oiUsd")),
        )
