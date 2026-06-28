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


_TICKERS = {
    "BTC/USDT": {"last": 60000.0, "percentage": 2.5, "quoteVolume": 9e9},
    "ETH/USDT": {"last": 3000.0, "percentage": -1.0, "quoteVolume": 5e9},
    "SOL/USDT": {"last": 150.0, "percentage": 8.0, "quoteVolume": 1e9},
    "ADA/USDT": {"last": 0.4, "percentage": -3.0, "quoteVolume": 2e8},
    "ETH/BTC": {"last": 0.05, "percentage": 0.5, "quoteVolume": 1e6},  # wrong quote, excluded
}


def _movers_source():
    async def fetch_tickers() -> dict:
        return _TICKERS

    return CcxtMarketData(fetch_tickers=fetch_tickers)


async def test_movers_gainers_sorted_and_quote_filtered():
    result = await _movers_source().get_movers("gainers", limit=3)
    assert result.category == "gainers"
    assert [m.base for m in result.movers] == ["SOL", "BTC", "ETH"]  # 8% > 2.5% > -1%
    assert all(m.symbol.endswith("/USDT") for m in result.movers)  # ETH/BTC excluded


async def test_movers_losers_and_most_active():
    losers = await _movers_source().get_movers("losers", limit=2)
    assert [m.base for m in losers.movers] == ["ADA", "ETH"]  # -3% then -1%
    active = await _movers_source().get_movers("most_active", limit=2)
    assert [m.base for m in active.movers] == ["BTC", "ETH"]  # by quote volume


async def test_movers_rejects_bad_category():
    with pytest.raises(ValueError):
        await _movers_source().get_movers("biggest")


async def test_order_book_spread_and_depth():
    async def fetch_order_book(symbol: str, limit: int) -> dict:
        return {
            "bids": [[100.0, 2.0], [99.0, 3.0]],
            "asks": [[101.0, 1.0], [102.0, 4.0]],
        }

    book = await CcxtMarketData(fetch_order_book=fetch_order_book).get_order_book("BTC/USDT")
    assert book.bid == Decimal("100.0")
    assert book.ask == Decimal("101.0")
    assert book.spread == Decimal("1.0")
    assert book.bid_depth_base == Decimal("5.0")  # 2 + 3
    assert book.ask_depth_base == Decimal("5.0")  # 1 + 4
    assert book.levels == 2
    assert book.imbalance == Decimal("0.0000")  # balanced depth → no directional pressure
    # microprice = (bid*ask_size + ask*bid_size)/(bid_size+ask_size) = (100*1 + 101*2)/3
    assert book.microprice == Decimal("100.66666667")


async def test_order_book_imbalance_and_microprice_asymmetric():
    async def fetch_order_book(symbol: str, limit: int) -> dict:
        return {
            "bids": [[100.0, 8.0], [99.0, 2.0]],  # heavy bid depth (10)
            "asks": [[101.0, 1.0], [102.0, 1.0]],  # thin ask depth (2)
        }

    book = await CcxtMarketData(fetch_order_book=fetch_order_book).get_order_book("BTC/USDT")
    assert book.imbalance == Decimal("0.6667")  # (10 − 2) / 12 → strong bid-side pressure
    # microprice leans toward the thin ask: (100*1 + 101*8)/(8+1) = 908/9 ≈ 100.889 > mid 100.5
    assert book.microprice == Decimal("100.88888889")
