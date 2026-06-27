"""CCXT implementation of ``CryptoMarketDataSource`` — keyless public crypto market data.

CCXT unifies ~100 exchanges behind one interface; its public market-data endpoints
(``fetch_ticker`` / ``fetch_ohlcv``) need NO API key, which keeps Scout in the keyless-first
spirit and mirrors the execution side (which already depends on CCXT). The exchange is
configurable (``SCOUT_CRYPTO_EXCHANGE``, default ``binance``); symbols use the CCXT unified
``BASE/QUOTE`` format so a researched asset maps straight to a tradable pair.

The raw exchange calls are injected (``fetch_ticker`` / ``fetch_ohlcv``) so the unit tests run
fully offline, with no network and no ccxt import.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from ...domain.models import CryptoBar, CryptoPriceHistory, CryptoQuote

TickerFetch = Callable[[str], Awaitable[dict]]
OhlcvFetch = Callable[[str, str, int], Awaitable[list]]


def normalize_pair(raw: str, default_quote: str) -> tuple[str, str, str]:
    """Normalize user input to a CCXT pair. Returns ``(symbol, base, quote)``.

    Accepts ``BTC``, ``btc``, ``BTC/USDT``, ``BTC-USD``, ``BTC_USDT``. When no quote is given,
    ``default_quote`` is used (so "BTC" → "BTC/USDT").
    """
    cleaned = raw.strip().upper().replace("-", "/").replace("_", "/")
    if "/" in cleaned:
        base, _, quote = cleaned.partition("/")
    else:
        base, quote = cleaned, default_quote
    base = base.strip()
    quote = quote.strip() or default_quote
    if not base:
        raise ValueError(f"Could not parse a crypto base asset from {raw!r}.")
    return f"{base}/{quote}", base, quote


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _ms_to_datetime(ms: Any) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=UTC)
    except (TypeError, ValueError, OverflowError):
        return None


class CcxtMarketData:
    def __init__(
        self,
        exchange: str = "binance",
        quote_ccy: str = "USDT",
        fetch_ticker: TickerFetch | None = None,
        fetch_ohlcv: OhlcvFetch | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._exchange = exchange
        self._quote_ccy = quote_ccy
        self._timeout = timeout
        self._fetch_ticker = fetch_ticker or self._default_fetch_ticker
        self._fetch_ohlcv = fetch_ohlcv or self._default_fetch_ohlcv

    def _new_exchange(self):
        import ccxt.async_support as ccxt  # lazy import: tests inject and never hit this

        if not hasattr(ccxt, self._exchange):
            raise ValueError(f"Unknown crypto exchange {self._exchange!r}.")
        return getattr(ccxt, self._exchange)(
            {"enableRateLimit": True, "timeout": int(self._timeout * 1000)}
        )

    async def _default_fetch_ticker(self, symbol: str) -> dict:
        ex = self._new_exchange()
        try:
            return await ex.fetch_ticker(symbol)
        finally:
            await ex.close()

    async def _default_fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> list:
        ex = self._new_exchange()
        try:
            return await ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        finally:
            await ex.close()

    async def get_quote(self, symbol: str) -> CryptoQuote | None:
        pair, base, quote = normalize_pair(symbol, self._quote_ccy)
        ticker = await self._fetch_ticker(pair)
        if not ticker:
            return None
        last = ticker.get("last")
        if last is None:
            last = ticker.get("close")
        return CryptoQuote(
            symbol=pair,
            base=base,
            quote=quote,
            exchange=self._exchange,
            last=_dec(last),
            bid=_dec(ticker.get("bid")),
            ask=_dec(ticker.get("ask")),
            high_24h=_dec(ticker.get("high")),
            low_24h=_dec(ticker.get("low")),
            change_percent_24h=_dec(ticker.get("percentage")),
            base_volume_24h=_dec(ticker.get("baseVolume")),
            quote_volume_24h=_dec(ticker.get("quoteVolume")),
            timestamp=_ms_to_datetime(ticker.get("timestamp")),
        )

    async def get_price_history(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 200,
        as_of: date | None = None,
    ) -> CryptoPriceHistory | None:
        pair, base, quote = normalize_pair(symbol, self._quote_ccy)
        capped = max(1, min(int(limit), 1000))
        rows = await self._fetch_ohlcv(pair, timeframe, capped)
        if rows is None:
            return None
        bars: list[CryptoBar] = []
        for row in rows:
            if not row or len(row) < 5:
                continue
            stamp = _ms_to_datetime(row[0])
            if stamp is None:
                continue
            if as_of is not None and stamp.date() > as_of:
                continue
            bars.append(
                CryptoBar(
                    timestamp=stamp,
                    open=_dec(row[1]),
                    high=_dec(row[2]),
                    low=_dec(row[3]),
                    close=_dec(row[4]),
                    volume=_dec(row[5]) if len(row) > 5 else None,
                )
            )
        return CryptoPriceHistory(
            symbol=pair,
            base=base,
            quote=quote,
            exchange=self._exchange,
            timeframe=timeframe,
            bars=bars,
            as_of=as_of,
        )
