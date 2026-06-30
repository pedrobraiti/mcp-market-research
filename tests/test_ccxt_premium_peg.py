"""Offline unit tests for the CCXT-derived premium & stablecoin-peg adapters.

The CCXT exchange is never touched: ``CcxtMarketData`` accepts injected ``fetch_ticker`` /
``fetch_ohlcv`` callables, so these run with no network and no ccxt import.
"""

from datetime import UTC, datetime
from decimal import Decimal

from scout.adapters.ccxt import CcxtMarketData, CcxtPremium, CcxtStablecoinPeg
from scout.adapters.retry import SourceUnavailable


def _ms(day: int) -> int:
    return int(datetime(2026, 6, day, tzinfo=UTC).timestamp() * 1000)


def _ohlcv(closes: list[float], start_day: int = 1) -> list:
    return [
        [_ms(start_day + i), c, c, c, c, 1.0] for i, c in enumerate(closes)
    ]


def _market(
    exchange: str,
    quote: str,
    *,
    last: float | None = None,
    closes: list[float] | None = None,
    ticker_exc: Exception | None = None,
) -> CcxtMarketData:
    async def fetch_ticker(symbol: str) -> dict:
        if ticker_exc is not None:
            raise ticker_exc
        return {} if last is None else {"last": last}

    async def fetch_ohlcv(symbol: str, timeframe: str, limit: int) -> list:
        return _ohlcv(closes) if closes else []

    return CcxtMarketData(
        exchange=exchange, quote_ccy=quote, fetch_ticker=fetch_ticker, fetch_ohlcv=fetch_ohlcv
    )


class _BadSymbol(Exception):
    """Stands in for ccxt.BadSymbol — name matched structurally (not a throttle)."""


# --- coinbase_premium ----------------------------------------------------------------------


async def test_premium_math_basic():
    cb = _market("coinbase", "USD", last=101.0)
    bn = _market("binance", "USDT", last=100.0)
    result = await CcxtPremium(cb, bn).get_premium("BTC", 30)
    assert result.symbol == "BTC"
    assert result.coinbase_price == Decimal("101.0")
    assert result.binance_price == Decimal("100.0")
    assert result.premium_pct == Decimal("1.0")  # (101 − 100) / 100 × 100
    assert result.source_status is None
    assert result.as_of is not None


async def test_premium_one_venue_failure_is_unavailable():
    cb = _market("coinbase", "USD", ticker_exc=SourceUnavailable("rate_limited"))
    bn = _market("binance", "USDT", last=100.0)
    result = await CcxtPremium(cb, bn).get_premium("BTC")
    assert result.source_status == "unavailable: rate_limited"
    assert result.premium_pct is None  # never faked from a single leg
    assert result.premium_zscore is None


async def test_premium_zscore_null_under_min_points():
    cb = _market("coinbase", "USD", last=101.0, closes=[101.0, 102.0, 103.0])
    bn = _market("binance", "USDT", last=100.0, closes=[100.0, 100.0, 100.0])
    result = await CcxtPremium(cb, bn).get_premium("BTC")
    assert result.premium_pct == Decimal("1.0")  # latest still computes from the live quotes
    assert len(result.history) == 3  # aligned 3-day series
    assert result.premium_zscore is None  # < ~8 points


async def test_premium_zscore_numeric_with_clean_history():
    cb_closes = [100.0 + i for i in range(1, 11)]  # 101..110
    bn_closes = [100.0] * 10
    cb = _market("coinbase", "USD", last=110.0, closes=cb_closes)
    bn = _market("binance", "USDT", last=100.0, closes=bn_closes)
    result = await CcxtPremium(cb, bn).get_premium("BTC")
    assert len(result.history) == 10
    assert result.premium_zscore is not None
    assert result.premium_zscore > 0  # latest premium is the high end of a rising series


async def test_premium_symbol_not_listed_is_note_not_unavailable():
    cb = _market("coinbase", "USD", ticker_exc=_BadSymbol("no market"))
    bn = _market("binance", "USDT", last=100.0)
    result = await CcxtPremium(cb, bn).get_premium("FOO")
    assert result.source_status is None  # not a throttle
    assert result.premium_pct is None
    assert "not listed" in (result.note or "")
    assert "coinbase" in (result.note or "")


# --- stablecoin_peg ------------------------------------------------------------------------


def _peg_adapter(
    prices: dict[str, float], excs: dict[str, Exception] | None = None
) -> CcxtStablecoinPeg:
    excs = excs or {}

    def factory(venue: str) -> CcxtMarketData:
        async def fetch_ticker(symbol: str) -> dict:
            base = symbol.split("/")[0]
            if base in excs:
                raise excs[base]
            if base not in prices:
                raise _BadSymbol(symbol)  # venue does not list this pair
            return {"last": prices[base]}

        return CcxtMarketData(exchange=venue, quote_ccy="USD", fetch_ticker=fetch_ticker)

    return CcxtStablecoinPeg(market_factory=factory)


async def test_peg_math_in_band_and_depeg():
    adapter = _peg_adapter({"USDT": 0.9990, "USDC": 0.9930})
    result = await adapter.get_peg(["USDT", "USDC"])
    items = {i.symbol: i for i in result.items}
    assert items["USDT"].deviation_bps == Decimal("-10.0")
    assert items["USDT"].depeg is False
    assert items["USDT"].venue == "kraken"
    assert items["USDC"].deviation_bps == Decimal("-70.0")
    assert items["USDC"].depeg is True  # |−70| > 50 bps threshold
    assert result.source_status is None


async def test_peg_missing_symbol_omitted_with_note():
    adapter = _peg_adapter({"USDT": 1.0})  # USDC not listed
    result = await adapter.get_peg(["USDT", "USDC"])
    assert {i.symbol for i in result.items} == {"USDT"}
    assert "USDC" in (result.note or "")
    assert result.source_status is None


async def test_peg_fetch_error_is_unavailable():
    adapter = _peg_adapter({"USDT": 1.0}, excs={"USDT": SourceUnavailable("rate_limited")})
    result = await adapter.get_peg(["USDT"])
    assert result.source_status == "unavailable: rate_limited"
    assert result.items == []


async def test_peg_defaults_to_three_majors():
    adapter = _peg_adapter({"USDT": 1.0001, "USDC": 1.0, "DAI": 0.9995})
    result = await adapter.get_peg()
    assert {i.symbol for i in result.items} == {"USDT", "USDC", "DAI"}
    assert all(not i.depeg for i in result.items)
