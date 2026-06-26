from datetime import date, datetime, timedelta
from decimal import Decimal

from scout.domain.models import (
    CompanySnapshot,
    DividendHistory,
    EarningsInfo,
    Fundamentals,
    NewsItem,
    NewsList,
    Period,
    PriceBar,
    PriceHistory,
)
from scout.research import (
    build_calendar,
    build_classification,
    build_comparison,
    build_correlation,
    build_news_digest,
)


class FakeSource:
    """A market-data source backed by canned per-symbol data."""

    def __init__(
        self,
        snapshots=None,
        fundamentals=None,
        closes=None,
        news=None,
        earnings=None,
        dividends=None,
    ):
        self._snapshots = snapshots or {}
        self._fundamentals = fundamentals or {}
        self._closes = closes or {}
        self._news = news or {}
        self._earnings = earnings or {}
        self._dividends = dividends or {}

    async def get_snapshot(self, symbol, as_of=None):
        return self._snapshots.get(symbol)

    async def get_fundamentals(self, symbol, period=Period.ANNUAL, as_of=None):
        return self._fundamentals.get(symbol)

    async def get_price_history(self, symbol, range="6mo", interval="1d", as_of=None):
        closes = self._closes.get(symbol)
        if closes is None:
            return None
        base = date(2024, 1, 1)
        bars = [
            PriceBar(date=base + timedelta(days=i), close=Decimal(str(c)))
            for i, c in enumerate(closes)
        ]
        return PriceHistory(symbol=symbol, interval=interval, bars=bars, as_of=as_of)

    async def get_news(self, symbol, limit=10):
        return self._news.get(symbol, NewsList(symbol=symbol))

    async def get_earnings(self, symbol, as_of=None):
        return self._earnings.get(symbol, EarningsInfo(symbol=symbol))

    async def get_dividends(self, symbol, as_of=None):
        return self._dividends.get(symbol, DividendHistory(symbol=symbol))


async def test_comparison_builds_rows_in_parallel():
    source = FakeSource(
        snapshots={
            "AAPL": CompanySnapshot(
                symbol="AAPL", name="Apple", price=Decimal("230"), sector="Tech"
            ),
            "MSFT": CompanySnapshot(symbol="MSFT", name="Microsoft", price=Decimal("350")),
        },
        fundamentals={
            "AAPL": Fundamentals(symbol="AAPL", period=Period.ANNUAL, revenue=Decimal("391")),
        },
    )
    result = await build_comparison(source, ["aapl", "msft"])
    assert result.symbols == ["AAPL", "MSFT"]
    by_symbol = {r.symbol: r for r in result.rows}
    assert by_symbol["AAPL"].price == Decimal("230")
    assert by_symbol["AAPL"].revenue == Decimal("391")
    assert by_symbol["MSFT"].revenue is None  # no fundamentals provided


async def test_comparison_notes_missing_symbol():
    result = await build_comparison(FakeSource(), ["nope"])
    assert result.rows[0].note == "data unavailable"


async def test_correlation_matrix_perfect_and_diagonal():
    source = FakeSource(
        closes={
            "AAA": [10, 11, 12, 13, 14],
            "BBB": [20, 22, 24, 26, 28],  # same returns as AAA → correlation 1.0
        }
    )
    result = await build_correlation(source, ["AAA", "BBB"])
    assert result.days == 5
    assert result.matrix["AAA"]["AAA"] == 1.0
    assert result.matrix["AAA"]["BBB"] == 1.0
    assert result.matrix["BBB"]["AAA"] == 1.0


async def test_correlation_needs_two_symbols():
    result = await build_correlation(FakeSource(closes={"AAA": [1, 2, 3]}), ["AAA", "ZZZ"])
    assert result.matrix == {}
    assert any("at least two" in note.lower() for note in result.notes)


async def test_classification_in_batch():
    source = FakeSource(
        snapshots={
            "AAPL": CompanySnapshot(symbol="AAPL", sector="Tech", market_cap=Decimal("3e12")),
        }
    )
    result = await build_classification(source, ["aapl", "zzz"])
    by_symbol = {i.symbol: i for i in result.items}
    assert by_symbol["AAPL"].sector == "Tech"
    assert by_symbol["ZZZ"].note == "unavailable"


async def test_news_digest_merges_and_sorts():
    source = FakeSource(
        news={
            "AAPL": NewsList(
                symbol="AAPL",
                items=[NewsItem(title="older", published=datetime(2026, 6, 1))],
            ),
            "MSFT": NewsList(
                symbol="MSFT",
                items=[NewsItem(title="newer", published=datetime(2026, 6, 20))],
            ),
        }
    )
    result = await build_news_digest(source, ["AAPL", "MSFT"])
    assert [i.title for i in result.items] == ["newer", "older"]  # newest first
    assert result.items[0].symbol == "MSFT"


async def test_calendar_collects_future_events_sorted():
    source = FakeSource(
        earnings={"AAPL": EarningsInfo(symbol="AAPL", next_earnings_date=date(2026, 8, 1))},
        dividends={"KO": DividendHistory(symbol="KO", next_ex_dividend=date(2026, 7, 10))},
    )
    result = await build_calendar(source, ["AAPL", "KO"], as_of=date(2026, 6, 25))
    assert [(e.symbol, e.type, e.date) for e in result.events] == [
        ("KO", "ex_dividend", date(2026, 7, 10)),
        ("AAPL", "earnings", date(2026, 8, 1)),
    ]


async def test_calendar_drops_past_events():
    source = FakeSource(
        earnings={"AAPL": EarningsInfo(symbol="AAPL", next_earnings_date=date(2026, 5, 1))},
    )
    result = await build_calendar(source, ["AAPL"], as_of=date(2026, 6, 25))
    assert result.events == []
