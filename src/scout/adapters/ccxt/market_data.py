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

from ...domain.models import (
    CryptoBar,
    CryptoMover,
    CryptoMoversList,
    CryptoOrderBook,
    CryptoPriceHistory,
    CryptoQuote,
    OrderBookLevel,
)

TickerFetch = Callable[[str], Awaitable[dict]]
OhlcvFetch = Callable[[str, str, int], Awaitable[list]]
TickersFetch = Callable[[], Awaitable[dict]]
OrderBookFetch = Callable[[str, int], Awaitable[dict]]

_MOVER_CATEGORIES = ("gainers", "losers", "most_active")


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
        fetch_tickers: TickersFetch | None = None,
        fetch_order_book: OrderBookFetch | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._exchange = exchange
        self._quote_ccy = quote_ccy
        self._timeout = timeout
        self._fetch_ticker = fetch_ticker or self._default_fetch_ticker
        self._fetch_ohlcv = fetch_ohlcv or self._default_fetch_ohlcv
        self._fetch_tickers = fetch_tickers or self._default_fetch_tickers
        self._fetch_order_book = fetch_order_book or self._default_fetch_order_book

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

    async def _default_fetch_tickers(self) -> dict:
        ex = self._new_exchange()
        try:
            return await ex.fetch_tickers()
        finally:
            await ex.close()

    async def _default_fetch_order_book(self, symbol: str, limit: int) -> dict:
        ex = self._new_exchange()
        try:
            return await ex.fetch_order_book(symbol, limit=limit)
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

    async def get_movers(self, category: str = "gainers", limit: int = 20) -> CryptoMoversList:
        cat = category.strip().lower()
        if cat not in _MOVER_CATEGORIES:
            raise ValueError(f"category must be one of {_MOVER_CATEGORIES}.")
        tickers = await self._fetch_tickers() or {}
        suffix = f"/{self._quote_ccy}"
        rows: list[CryptoMover] = []
        for sym, ticker in tickers.items():
            if not isinstance(ticker, dict) or not str(sym).endswith(suffix):
                continue
            rows.append(
                CryptoMover(
                    symbol=str(sym),
                    base=str(sym)[: -len(suffix)],
                    last=_dec(ticker.get("last")),
                    change_percent_24h=_dec(ticker.get("percentage")),
                    quote_volume_24h=_dec(ticker.get("quoteVolume")),
                )
            )
        if cat == "most_active":
            rows.sort(key=lambda r: r.quote_volume_24h or Decimal(0), reverse=True)
        else:
            rows = [r for r in rows if r.change_percent_24h is not None]
            rows.sort(key=lambda r: r.change_percent_24h, reverse=(cat == "gainers"))
        return CryptoMoversList(
            category=cat,
            exchange=self._exchange,
            quote=self._quote_ccy,
            movers=rows[: max(1, min(int(limit), 100))],
        )

    async def get_order_book(self, symbol: str, limit: int = 20) -> CryptoOrderBook | None:
        pair, _, _ = normalize_pair(symbol, self._quote_ccy)
        capped = max(1, min(int(limit), 100))
        book = await self._fetch_order_book(pair, capped)
        if not book:
            return None
        bids = [lvl for lvl in (book.get("bids") or []) if lvl and len(lvl) >= 2]
        asks = [lvl for lvl in (book.get("asks") or []) if lvl and len(lvl) >= 2]
        best_bid = _dec(bids[0][0]) if bids else None
        best_ask = _dec(asks[0][0]) if asks else None
        spread = best_ask - best_bid if best_bid is not None and best_ask is not None else None
        mid = (
            (best_bid + best_ask) / 2
            if best_bid is not None and best_ask is not None
            else None
        )
        spread_pct = (
            (spread / mid * 100) if spread is not None and mid not in (None, Decimal(0)) else None
        )
        return CryptoOrderBook(
            symbol=pair,
            exchange=self._exchange,
            bid=best_bid,
            ask=best_ask,
            spread=spread,
            spread_percent=spread_pct,
            bid_depth_base=sum((_dec(lvl[1]) or Decimal(0)) for lvl in bids) or None,
            ask_depth_base=sum((_dec(lvl[1]) or Decimal(0)) for lvl in asks) or None,
            levels=max(len(bids), len(asks)),
            top_bids=[OrderBookLevel(price=_dec(lvl[0]), amount=_dec(lvl[1])) for lvl in bids[:10]],
            top_asks=[OrderBookLevel(price=_dec(lvl[0]), amount=_dec(lvl[1])) for lvl in asks[:10]],
        )
