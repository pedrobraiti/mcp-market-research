from datetime import date
from decimal import Decimal

import pytest

from scout.domain.models import (
    AnalystView,
    CompanySnapshot,
    DividendHistory,
    EarningsInfo,
    Fundamentals,
    NewsList,
    Period,
    PriceBar,
    PriceHistory,
)
from scout.research import build_dossier


class FakeSource:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def get_snapshot(self, symbol, as_of=None):
        self.calls.append("snapshot")
        return CompanySnapshot(symbol=symbol, price=Decimal("100"), as_of=as_of)

    async def get_fundamentals(self, symbol, period=Period.ANNUAL, as_of=None):
        self.calls.append("fundamentals")
        return Fundamentals(symbol=symbol, period=period, revenue=Decimal("1000"))

    async def get_dividends(self, symbol, as_of=None):
        self.calls.append("dividends")
        return DividendHistory(symbol=symbol, growth_streak_years=5)

    async def get_price_history(self, symbol, range="6mo", interval="1d", as_of=None):
        self.calls.append("price_history")
        bars = [
            PriceBar(
                date=date(2024, 1, 1),
                close=Decimal("100"),
                high=Decimal("101"),
                low=Decimal("99"),
            )
        ]
        return PriceHistory(symbol=symbol, interval=interval, bars=bars, as_of=as_of)

    async def get_earnings(self, symbol, as_of=None):
        self.calls.append("earnings")
        return EarningsInfo(symbol=symbol)

    async def get_analyst_view(self, symbol):
        self.calls.append("analyst")
        return AnalystView(symbol=symbol, recommendation_key="buy")

    async def get_news(self, symbol, limit=10):
        self.calls.append("news")
        return NewsList(symbol=symbol)


class PartialSource(FakeSource):
    async def get_fundamentals(self, symbol, period=Period.ANNUAL, as_of=None):
        raise RuntimeError("fundamentals source down")


async def test_dossier_full_gathers_everything():
    source = FakeSource()
    dossier = await build_dossier(source, "aapl")
    assert dossier.symbol == "AAPL"
    assert dossier.snapshot is not None and dossier.snapshot.price == Decimal("100")
    assert dossier.fundamentals is not None
    assert dossier.dividends is not None
    assert dossier.technicals is not None  # computed from the price history
    assert dossier.earnings is not None
    assert dossier.analyst is not None and dossier.analyst.recommendation_key == "buy"
    assert dossier.news is not None
    assert dossier.notes == []
    expected_calls = {
        "snapshot",
        "fundamentals",
        "dividends",
        "price_history",
        "earnings",
        "analyst",
        "news",
    }
    assert expected_calls <= set(source.calls)


async def test_dossier_summary_is_snapshot_only():
    source = FakeSource()
    dossier = await build_dossier(source, "AAPL", depth="summary")
    assert dossier.snapshot is not None
    assert dossier.fundamentals is None
    assert dossier.technicals is None
    assert source.calls == ["snapshot"]


async def test_dossier_degrades_on_partial_failure():
    dossier = await build_dossier(PartialSource(), "AAPL")
    assert dossier.snapshot is not None  # snapshot still came through
    assert dossier.fundamentals is None
    assert any("fundamentals unavailable" in note for note in dossier.notes)


async def test_dossier_passes_as_of_through():
    dossier = await build_dossier(FakeSource(), "AAPL", as_of=date(2024, 1, 2))
    assert dossier.as_of == date(2024, 1, 2)
    assert dossier.snapshot.as_of == date(2024, 1, 2)


async def test_dossier_rejects_bad_depth():
    with pytest.raises(ValueError):
        await build_dossier(FakeSource(), "AAPL", depth="everything")
