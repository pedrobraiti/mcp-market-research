from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
import pytest

from scout.adapters.yfinance import YFinanceMarketData
from scout.adapters.yfinance.market_data import _had_cut

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
    "recommendationKey": "buy",
    "recommendationMean": 2.1,
    "numberOfAnalystOpinions": 35,
    "targetMeanPrice": 290.0,
    "targetMedianPrice": 295.0,
    "targetHighPrice": 340.0,
    "targetLowPrice": 200.0,
}

_NEWS = [
    {
        "content": {
            "title": "Apple unveils new chip",
            "summary": "The company announced a faster processor.",
            "canonicalUrl": {"url": "https://news.example/aapl-chip"},
            "provider": {"displayName": "Reuters"},
            "pubDate": "2026-06-20T14:30:00Z",
        }
    }
]

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


_SPLITS = pd.Series(
    {
        pd.Timestamp("2014-06-09"): 7.0,
        pd.Timestamp("2020-08-31"): 4.0,
    }
)


class FakeTicker:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.info = _INFO
        self.dividends = _DIVIDENDS
        self.splits = _SPLITS
        self.income_stmt = _INCOME
        self.quarterly_income_stmt = _INCOME
        self.balance_sheet = _BALANCE
        self.quarterly_balance_sheet = _BALANCE
        self.cashflow = _CASHFLOW
        self.quarterly_cashflow = _CASHFLOW
        self.news = _NEWS

    def get_earnings_dates(self, limit=12):
        return pd.DataFrame(
            {
                "EPS Estimate": [1.50, 1.40],
                "Reported EPS": [float("nan"), 1.46],
                "Surprise(%)": [float("nan"), 4.3],
            },
            index=[pd.Timestamp("2026-08-01"), pd.Timestamp("2026-05-01")],
        )

    def history(self, period=None, interval=None, start=None, end=None, **kwargs):
        return pd.DataFrame(
            {
                "Open": [220.0, 221.5],
                "High": [222.0, 224.0],
                "Low": [219.0, 221.0],
                "Close": [221.0, 223.5],
                "Volume": [1_000_000, 1_100_000],
            },
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


async def test_snapshot_surfaces_only_recent_splits_newest_first():
    today = date.today()
    recent = today - timedelta(days=120)
    older_but_recent = today - timedelta(days=600)
    ancient = today - timedelta(days=365 * 10)

    class RecentAndAncientSplitTicker(FakeTicker):
        def __init__(self, symbol):
            super().__init__(symbol)
            self.splits = pd.Series(
                {
                    pd.Timestamp(ancient): 7.0,
                    pd.Timestamp(older_but_recent): 3.0,
                    pd.Timestamp(recent): 10.0,
                }
            )

    source = YFinanceMarketData(ticker_factory=RecentAndAncientSplitTicker)
    snapshot = await source.get_snapshot("NFLX")
    assert snapshot is not None
    assert [s.date for s in snapshot.recent_splits] == [recent, older_but_recent]
    assert snapshot.recent_splits[0].ratio == Decimal("10.0")


async def test_snapshot_excludes_decades_old_splits():
    # The default fake ticker only ever split in 2014/2020 — ancient as of today.
    snapshot = await _source().get_snapshot("AAPL")
    assert snapshot is not None
    assert snapshot.recent_splits == []


async def test_snapshot_as_of_windows_splits_around_as_of():
    as_of = date(2024, 1, 1)
    in_window = date(2023, 6, 1)  # within ~24 months before as_of
    after_as_of = date(2024, 6, 1)  # later than as_of -> excluded
    ancient = date(2014, 6, 9)  # decades before as_of -> excluded

    class AsOfSplitTicker(FakeTicker):
        def __init__(self, symbol):
            super().__init__(symbol)
            self.splits = pd.Series(
                {
                    pd.Timestamp(ancient): 7.0,
                    pd.Timestamp(in_window): 4.0,
                    pd.Timestamp(after_as_of): 2.0,
                }
            )

    source = YFinanceMarketData(ticker_factory=AsOfSplitTicker)
    snapshot = await source.get_snapshot("X", as_of=as_of)
    assert snapshot is not None
    assert [s.date for s in snapshot.recent_splits] == [in_window]


async def test_snapshot_splits_empty_when_none():
    class NoSplitsTicker(FakeTicker):
        def __init__(self, symbol):
            super().__init__(symbol)
            self.splits = pd.Series(dtype=float)

    snapshot = await YFinanceMarketData(ticker_factory=NoSplitsTicker).get_snapshot("AAPL")
    assert snapshot is not None
    assert snapshot.recent_splits == []


async def test_snapshot_splits_failure_does_not_break_snapshot():
    class BrokenSplitsTicker(FakeTicker):
        @property
        def splits(self):
            raise RuntimeError("splits fetch blew up")

        @splits.setter
        def splits(self, value):
            pass

    snapshot = await YFinanceMarketData(ticker_factory=BrokenSplitsTicker).get_snapshot("AAPL")
    assert snapshot is not None
    assert snapshot.price == Decimal("230.0")
    assert snapshot.recent_splits == []


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


def test_had_cut_ignores_incomplete_current_year():
    # Rising every complete year; the current (partial) year sums lower only because it has
    # fewer ex-dates so far — must NOT be flagged as a cut. (The Micron mid-year false positive.)
    annual = {
        2021: Decimal("0.40"),
        2022: Decimal("0.46"),
        2023: Decimal("0.46"),
        2024: Decimal("0.49"),
        2025: Decimal("0.49"),
        2026: Decimal("0.15"),  # partial year-to-date
    }
    assert _had_cut(annual, current_year=2026) is False


def test_had_cut_detects_real_adjacent_cut_between_complete_years():
    annual = {2022: Decimal("0.46"), 2023: Decimal("0.30"), 2024: Decimal("0.30")}
    assert _had_cut(annual, current_year=2026) is True


def test_had_cut_ignores_multi_year_gap():
    # Paid in the 1990s, suspended, resumed decades later — a gap is not a cut.
    annual = {1995: Decimal("0.20"), 2021: Decimal("0.10"), 2022: Decimal("0.12")}
    assert _had_cut(annual, current_year=2026) is False


async def test_dividends_as_of_filters_and_recomputes():
    history = await _source().get_dividends("AAPL", as_of=date(2022, 12, 31))
    assert history is not None
    assert len(history.payments) == 2
    assert history.trailing_12m == Decimal("0.23")
    # Only one complete prior year (2021) remains, so a streak can't be established.
    assert history.growth_streak_years is None


async def test_price_history_parses_ohlcv_bars():
    history = await _source().get_price_history("AAPL", "1mo", "1d")
    assert history is not None
    assert history.interval == "1d"
    assert len(history.bars) == 2
    last = history.bars[1]
    assert last.date == date(2024, 6, 11)
    assert last.close == Decimal("223.5")
    assert last.high == Decimal("224.0")
    assert last.volume == 1_100_000


async def test_price_history_as_of_truncates():
    history = await _source().get_price_history("AAPL", "1mo", "1d", as_of=date(2024, 6, 10))
    assert history is not None
    assert len(history.bars) == 1
    assert history.bars[0].date == date(2024, 6, 10)


async def test_news_parses_items():
    news = await _source().get_news("AAPL")
    assert news is not None
    assert len(news.items) == 1
    item = news.items[0]
    assert item.title == "Apple unveils new chip"
    assert item.publisher == "Reuters"
    assert "news.example/aapl-chip" in item.url
    assert item.published is not None and item.published.year == 2026


async def test_earnings_splits_future_and_past():
    info = await _source().get_earnings("AAPL", as_of=date(2026, 6, 25))
    assert info.next_earnings_date == date(2026, 8, 1)
    future = [e for e in info.events if e.is_future]
    past = [e for e in info.events if not e.is_future]
    assert any(e.event_date == date(2026, 8, 1) for e in future)
    assert any(e.eps_reported == Decimal("1.46") for e in past)


async def test_analyst_view_reports_consensus():
    view = await _source().get_analyst_view("AAPL")
    assert view is not None
    assert view.recommendation_key == "buy"
    assert view.number_of_analysts == 35
    assert view.target_mean == Decimal("290.0")
    assert view.target_high == Decimal("340.0")


async def test_options_volatility_expected_move():
    calls = pd.DataFrame({"strike": [240.0, 250.0, 260.0], "impliedVolatility": [0.40, 0.30, 0.42]})
    puts = pd.DataFrame({"strike": [240.0, 250.0, 260.0], "impliedVolatility": [0.41, 0.32, 0.43]})

    class _Chain:
        def __init__(self):
            self.calls = calls
            self.puts = puts

    class OptionsTicker:
        def __init__(self, symbol):
            self.info = {"currentPrice": 250.0}
            self.options = ["2026-07-10", "2026-08-21"]

        def option_chain(self, expiry):
            return _Chain()

    source = YFinanceMarketData(ticker_factory=OptionsTicker)
    vol = await source.get_options_volatility("AAPL")
    assert vol is not None
    assert vol.expiry == date(2026, 7, 10)  # nearest expiry chosen
    assert vol.atm_strike == Decimal("250.0")  # closest strike to 250 price
    assert vol.atm_iv == Decimal("0.31")  # avg of ATM call 0.30 and put 0.32
    assert vol.current_price == Decimal("250.0")
    assert vol.expected_move_percent is not None and vol.expected_move_percent > Decimal("0")
    assert vol.expected_move_low < Decimal("250") < vol.expected_move_high


async def test_options_volatility_none_without_chain():
    source = YFinanceMarketData(ticker_factory=FakeTicker)  # no options attribute
    assert await source.get_options_volatility("AAPL") is None


async def test_ownership_parses_holders_and_insiders():
    class OwnershipTicker:
        def __init__(self, symbol):
            self.major_holders = pd.DataFrame(
                {"Value": [0.0007, 0.62]},
                index=["insidersPercentHeld", "institutionsPercentHeld"],
            )
            self.institutional_holders = pd.DataFrame(
                {
                    "Holder": ["Vanguard", "BlackRock"],
                    "Shares": [1_000_000_000, 900_000_000],
                    "Value": [3.0e11, 2.7e11],
                    "pctHeld": [0.08, 0.07],
                }
            )
            self.insider_transactions = pd.DataFrame(
                {
                    "Insider": ["Tim Cook"],
                    "Position": ["CEO"],
                    "Transaction": ["Sale"],
                    "Shares": [50_000],
                    "Value": [1.2e7],
                    "Start Date": [pd.Timestamp("2026-05-10")],
                }
            )

    source = YFinanceMarketData(ticker_factory=OwnershipTicker)
    owner = await source.get_ownership("AAPL")
    assert owner is not None
    assert owner.insider_percent == Decimal("0.0007")
    assert owner.institution_percent == Decimal("0.62")
    assert owner.institutional_holders[0].holder == "Vanguard"
    assert owner.institutional_holders[0].pct_out == Decimal("0.08")
    assert owner.insider_transactions[0].insider == "Tim Cook"
    assert owner.insider_transactions[0].transaction_date == date(2026, 5, 10)


async def test_ownership_none_when_unavailable():
    assert await YFinanceMarketData(ticker_factory=FakeTicker).get_ownership("AAPL") is None


async def test_etf_holdings_parses_funds_data():
    class _FundsData:
        top_holdings = pd.DataFrame(
            {"Name": ["Apple", "Microsoft"], "Holding Percent": [0.071, 0.063]},
            index=["AAPL", "MSFT"],
        )
        sector_weightings = {"technology": 0.30, "financial_services": 0.13}

    class EtfTicker:
        def __init__(self, symbol):
            self.funds_data = _FundsData()

    source = YFinanceMarketData(ticker_factory=EtfTicker)
    holdings = await source.get_etf_holdings("XLK")
    assert holdings is not None
    assert holdings.top_holdings[0].symbol == "AAPL"
    assert holdings.top_holdings[0].weight == Decimal("0.071")
    assert holdings.sector_weights["technology"] == Decimal("0.3")


async def test_etf_holdings_none_for_non_fund():
    source = YFinanceMarketData(ticker_factory=FakeTicker)  # no funds_data attribute
    assert await source.get_etf_holdings("AAPL") is None


async def test_quality_metrics_ratios_and_cagr():
    # _INFO lacks the ratio keys, so add them via a custom ticker.
    class QualityTicker(FakeTicker):
        def __init__(self, symbol):
            super().__init__(symbol)
            self.info = {
                **_INFO,
                "returnOnEquity": 1.5,
                "returnOnAssets": 0.3,
                "grossMargins": 0.46,
                "profitMargins": 0.24,
                "revenueGrowth": 0.08,
            }

    source = YFinanceMarketData(ticker_factory=QualityTicker)
    metrics = await source.get_quality_metrics("AAPL")
    assert metrics is not None
    assert metrics.roe == Decimal("1.5")
    assert metrics.gross_margin == Decimal("0.46")
    assert metrics.revenue_growth_yoy == Decimal("0.08")
    # _INCOME has FY2024 revenue 391035 and FY2023 383285 → 1-period CAGR ~2.02%.
    assert metrics.cagr_years == 1
    assert metrics.revenue_cagr is not None
    assert Decimal("0.01") < metrics.revenue_cagr < Decimal("0.03")


async def test_market_movers_parses_screen():
    screen_result = {
        "quotes": [
            {
                "symbol": "ABCD",
                "shortName": "Abcd Inc",
                "regularMarketPrice": 12.5,
                "regularMarketChangePercent": 18.4,
                "regularMarketVolume": 5_000_000,
            },
            {"no_symbol": True},
        ]
    }
    source = YFinanceMarketData(screen_fn=lambda key: screen_result)
    result = await source.get_movers("gainers", 10)
    assert result.category == "gainers"
    assert len(result.movers) == 1
    assert result.movers[0].symbol == "ABCD"
    assert result.movers[0].change_percent == Decimal("18.4")
    assert result.movers[0].volume == 5_000_000

    with pytest.raises(ValueError):
        await source.get_movers("nonsense")


async def test_search_symbols_parses_quotes():
    quotes = [
        {"symbol": "AAPL", "shortname": "Apple Inc.", "exchange": "NMS", "quoteType": "EQUITY"},
        {"symbol": "APLE", "longname": "Apple Hospitality REIT", "quoteType": "EQUITY"},
        {"no_symbol": True},  # malformed entry should be skipped
    ]
    source = YFinanceMarketData(search_fn=lambda q: quotes)
    result = await source.search_symbols("apple", limit=10)
    assert result.query == "apple"
    assert len(result.matches) == 2
    assert result.matches[0].symbol == "AAPL"
    assert result.matches[0].name == "Apple Inc."
    assert result.matches[1].name == "Apple Hospitality REIT"


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
