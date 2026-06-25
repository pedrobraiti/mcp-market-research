from datetime import date
from decimal import Decimal

import pytest

from scout.domain.models import CompanySnapshot, DividendHistory, Fundamentals, Period
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


class PartialSource(FakeSource):
    async def get_fundamentals(self, symbol, period=Period.ANNUAL, as_of=None):
        raise RuntimeError("fundamentals source down")


async def test_dossier_full_gathers_all_three():
    source = FakeSource()
    dossier = await build_dossier(source, "aapl")
    assert dossier.symbol == "AAPL"
    assert dossier.snapshot is not None and dossier.snapshot.price == Decimal("100")
    assert dossier.fundamentals is not None
    assert dossier.dividends is not None
    assert dossier.notes == []
    assert set(source.calls) == {"snapshot", "fundamentals", "dividends"}


async def test_dossier_summary_is_snapshot_only():
    source = FakeSource()
    dossier = await build_dossier(source, "AAPL", depth="summary")
    assert dossier.snapshot is not None
    assert dossier.fundamentals is None
    assert dossier.dividends is None
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
