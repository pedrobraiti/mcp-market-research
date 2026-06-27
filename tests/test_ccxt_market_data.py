from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from scout.adapters.ccxt import CcxtMarketData, normalize_pair


def _ms(year: int, month: int, day: int) -> int:
    return int(datetime(year, month, day, tzinfo=UTC).timestamp() * 1000)


_TICKER = {
    "symbol": "BTC/USDT",
    "timestamp": _ms(2026, 6, 25),
    "high": 68000.0,
    "low": 66000.0,
    "bid": 67000.0,
    "ask": 67010.0,
    "last": 67005.0,
    "close": 67005.0,
    "baseVolume": 1234.5,
    "quoteVolume": 83000000.0,
    "percentage": 1.5,
}

_OHLCV = [
    [_ms(2026, 6, 23), 66000.0, 66800.0, 65500.0, 66500.0, 1000.0],
    [_ms(2026, 6, 24), 66500.0, 67200.0, 66100.0, 67000.0, 1100.0],
    [_ms(2026, 6, 25), 67000.0, 68000.0, 66000.0, 67005.0, 1234.5],
]


def test_normalize_pair_variants():
    assert normalize_pair("BTC", "USDT") == ("BTC/USDT", "BTC", "USDT")
    assert normalize_pair("btc", "USDT") == ("BTC/USDT", "BTC", "USDT")
    assert normalize_pair("ETH/USD", "USDT") == ("ETH/USD", "ETH", "USD")
    assert normalize_pair("sol-usdc", "USDT") == ("SOL/USDC", "SOL", "USDC")


def test_normalize_pair_rejects_empty_base():
    with pytest.raises(ValueError):
        normalize_pair("/USDT", "USDT")


async def test_get_quote_builds_model():
    async def fetch_ticker(symbol: str) -> dict:
        assert symbol == "BTC/USDT"
        return _TICKER

    quote = await CcxtMarketData(fetch_ticker=fetch_ticker).get_quote("btc")
    assert quote is not None
    assert quote.symbol == "BTC/USDT"
    assert quote.base == "BTC"
    assert quote.quote == "USDT"
    assert quote.exchange == "binance"
    assert quote.last == Decimal("67005.0")
    assert quote.change_percent_24h == Decimal("1.5")
    assert quote.timestamp == datetime(2026, 6, 25, tzinfo=UTC)


async def test_get_quote_falls_back_to_close_when_last_missing():
    ticker = dict(_TICKER, last=None)

    async def fetch_ticker(symbol: str) -> dict:
        return ticker

    quote = await CcxtMarketData(fetch_ticker=fetch_ticker).get_quote("BTC/USDT")
    assert quote.last == Decimal("67005.0")  # came from "close"


async def test_get_quote_none_when_empty_ticker():
    async def fetch_ticker(symbol: str) -> dict:
        return {}

    assert await CcxtMarketData(fetch_ticker=fetch_ticker).get_quote("BTC") is None


async def test_get_price_history_builds_bars():
    async def fetch_ohlcv(symbol: str, timeframe: str, limit: int) -> list:
        assert symbol == "BTC/USDT"
        assert timeframe == "1d"
        return _OHLCV

    history = await CcxtMarketData(fetch_ohlcv=fetch_ohlcv).get_price_history("BTC", "1d", 200)
    assert history is not None
    assert history.base == "BTC"
    assert len(history.bars) == 3
    assert history.bars[-1].close == Decimal("67005.0")
    assert history.bars[0].timestamp == datetime(2026, 6, 23, tzinfo=UTC)


async def test_get_price_history_as_of_truncates():
    async def fetch_ohlcv(symbol: str, timeframe: str, limit: int) -> list:
        return _OHLCV

    history = await CcxtMarketData(fetch_ohlcv=fetch_ohlcv).get_price_history(
        "BTC", "1d", 200, as_of=date(2026, 6, 24)
    )
    assert [b.timestamp.date() for b in history.bars] == [date(2026, 6, 23), date(2026, 6, 24)]
