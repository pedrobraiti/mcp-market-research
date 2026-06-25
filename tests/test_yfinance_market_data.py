from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from scout.adapters.yfinance import YFinanceMarketData

_INFO = {
    "longName": "Apple Inc.",
    "shortName": "Apple",
    "currency": "USD",
    "currentPrice": 230.0,
    "previousClose": 228.0,
    "marketCap": 3_500_000_000_000,
    "trailingPE": 35.5,
    "forwardPE": 30.1,
    "dividendYield": 0.0044,
    "fiftyTwoWeekHigh": 260.1,
    "fiftyTwoWeekLow": 164.0,
    "sector": "Technology",
    "industry": "Consumer Electronics",
}

_INCOME = pd.DataFrame(
    {
        pd.Timestamp("2024-09-30"): {
            "Total Revenue": 391_035_000_000.0,
            "Gross Profit": 180_683_000_000.0,
            "Operating Income": 123_216_000_000.0,
            "Net Income": 93_736_000_000.0,
        },
        pd.Timestamp("2023-09-30"): {
            "Total Revenue": 383_285_000_000.0,
            "Gross Profit": 169_148_000_000.0,
            "Operating Income": 114_301_000_000.0,
            "Net Income": 96_995_000_000.0,
        },
    }
)

_BALANCE = pd.DataFrame(
    {
        pd.Timestamp("2024-09-30"): {
            "Total Debt": 106_629_000_000.0,
            "Cash And Cash Equivalents": 29_943_000_000.0,
        }
    }
)

_CASHFLOW = pd.DataFrame(
    {pd.Timestamp("2024-09-30"): {"Free Cash Flow": 108_807_000_000.0}}
)

_DIVIDENDS = pd.Series(
    {
        pd.Timestamp("2021-08-06"): 0.205,
        pd.Timestamp("2022-08-05"): 0.23,
        pd.Timestamp("2023-08-11"): 0.24,
        pd.Timestamp("2024-08-12"): 0.25,
    }
)


class FakeTicker:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.info = _INFO
        self.dividends = _DIVIDENDS
        self.income_stmt = _INCOME
        self.quarterly_income_stmt = _INCOME
        self.balance_sheet = _BALANCE
        self.quarterly_balance_sheet = _BALANCE
        self.cashflow = _CASHFLOW
        self.quarterly_cashflow = _CASHFLOW

    def history(self, start=None, end=None):
        return pd.DataFrame(
            {"Close": [221.0, 223.5]},
            index=[pd.Timestamp("2024-06-10"), pd.Timestamp("2024-06-11")],
        )


class EmptyTicker:
    def __init__(self, symbol: str) -> None:
        self.info = {}
        self.dividends = pd.Series(dtype=float)

    def history(self, start=None, end=None):
        return pd.DataFrame()


class FlakyTicker:
    """Raises on `.info` the first ``fail_times`` accesses, then succeeds — to test retry."""

    fail_times = 2
    accesses = {"n": 0}

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.dividends = _DIVIDENDS

    @property
    def info(self):
        FlakyTicker.accesses["n"] += 1
        if FlakyTicker.accesses["n"] <= FlakyTicker.fail_times:
            raise RuntimeError("rate limited")
        return _INFO


def _source():
    return YFinanceMarketData(ticker_factory=FakeTicker)


async def test_snapshot_parses_price_and_multiples():
    snapshot = await _source().get_snapshot("aapl")
    assert snapshot is not None
    assert snapshot.symbol == "AAPL"
    assert snapshot.name == "Apple Inc."
    assert snapshot.price == Decimal("230.0")
    assert snapshot.change == Decimal("2.0")
    assert snapshot.change_percent is not None
    assert Decimal("0.8") < snapshot.change_percent < Decimal("0.9")
    assert snapshot.market_cap == Decimal("3500000000000")
    assert snapshot.sector == "Technology"
    assert snapshot.as_of is None


async def test_snapshot_with_as_of_uses_history_close():
    snapshot = await _source().get_snapshot("AAPL", as_of=date(2024, 6, 11))
    assert snapshot is not None
    assert snapshot.price == Decimal("223.5")
    assert snapshot.previous_close == Decimal("221.0")
    assert snapshot.as_of == date(2024, 6, 11)


async def test_snapshot_unresolved_symbol_returns_none():
    source = YFinanceMarketData(ticker_factory=EmptyTicker)
    assert await source.get_snapshot("NOPE") is None


async def test_fundamentals_picks_latest_period_and_derives_margins():
    fundamentals = await _source().get_fundamentals("AAPL")
    assert fundamentals is not None
    assert fundamentals.fiscal_period_end == date(2024, 9, 30)
    assert fundamentals.revenue == Decimal("391035000000")
    assert fundamentals.total_debt == Decimal("106629000000")
    assert fundamentals.free_cash_flow == Decimal("108807000000")
    assert fundamentals.gross_margin is not None
    assert Decimal("0.46") < fundamentals.gross_margin < Decimal("0.47")


async def test_fundamentals_as_of_selects_older_period():
    fundamentals = await _source().get_fundamentals("AAPL", as_of=date(2023, 12, 31))
    assert fundamentals is not None
    assert fundamentals.fiscal_period_end == date(2023, 9, 30)
    assert fundamentals.revenue == Decimal("383285000000")


async def test_dividends_streak_and_no_cut():
    history = await _source().get_dividends("AAPL")
    assert history is not None
    assert len(history.payments) == 4
    assert history.growth_streak_years == 3
    assert history.had_cut is False


async def test_dividends_as_of_filters_and_recomputes():
    history = await _source().get_dividends("AAPL", as_of=date(2022, 12, 31))
    assert history is not None
    assert len(history.payments) == 2
    assert history.trailing_12m == Decimal("0.23")
    # Only one complete prior year (2021) remains, so a streak can't be established.
    assert history.growth_streak_years is None


async def test_retry_recovers_from_transient_failure():
    FlakyTicker.accesses["n"] = 0
    FlakyTicker.fail_times = 2
    source = YFinanceMarketData(ticker_factory=FlakyTicker, retry_attempts=3, retry_base_delay=0)
    snapshot = await source.get_snapshot("AAPL")
    assert snapshot is not None
    assert snapshot.price == Decimal("230.0")
    assert FlakyTicker.accesses["n"] == 3  # failed twice, succeeded on the third


async def test_retry_gives_up_and_raises_after_exhaustion():
    FlakyTicker.accesses["n"] = 0
    FlakyTicker.fail_times = 99
    source = YFinanceMarketData(ticker_factory=FlakyTicker, retry_attempts=2, retry_base_delay=0)
    with pytest.raises(RuntimeError, match="rate limited"):
        await source.get_snapshot("AAPL")
