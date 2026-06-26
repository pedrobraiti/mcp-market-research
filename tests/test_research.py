from datetime import date, timedelta
from decimal import Decimal

from scout.domain.models import CompanySnapshot, Fundamentals, Period, PriceBar, PriceHistory
from scout.research import build_comparison, build_correlation


class FakeSource:
    """A market-data source backed by canned per-symbol data."""

    def __init__(self, snapshots=None, fundamentals=None, closes=None):
        self._snapshots = snapshots or {}
        self._fundamentals = fundamentals or {}
        self._closes = closes or {}

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
