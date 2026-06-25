from datetime import date
from decimal import Decimal

import pytest

from scout.config import get_settings
from scout.domain.models import CompanySnapshot, DividendHistory, Fundamentals, Period
from scout.server import app as app_module
from scout.server.services import Services


class FakeSource:
    async def get_snapshot(self, symbol, as_of=None):
        return CompanySnapshot(symbol=symbol.upper(), price=Decimal("100"), as_of=as_of)

    async def get_fundamentals(self, symbol, period=Period.ANNUAL, as_of=None):
        return Fundamentals(symbol=symbol.upper(), period=period, revenue=Decimal("1000"))

    async def get_dividends(self, symbol, as_of=None):
        return DividendHistory(symbol=symbol.upper(), growth_streak_years=10)


class BrokenSource(FakeSource):
    async def get_snapshot(self, symbol, as_of=None):
        raise RuntimeError("data source down")


@pytest.fixture
def use_source():
    previous = app_module._services

    def _install(source):
        app_module._services = Services(settings=get_settings(), market_data=source)

    yield _install
    app_module._services = previous


async def test_company_snapshot_envelope(use_source):
    use_source(FakeSource())
    result = await app_module.company_snapshot("aapl")
    assert result["ok"] is True
    assert result["data"]["symbol"] == "AAPL"
    assert result["data"]["price"] == "100"


async def test_company_snapshot_parses_as_of(use_source):
    use_source(FakeSource())
    result = await app_module.company_snapshot("aapl", as_of="2024-01-15")
    assert result["ok"] is True
    assert result["data"]["as_of"] == "2024-01-15"


async def test_fundamentals_rejects_bad_period(use_source):
    use_source(FakeSource())
    result = await app_module.fundamentals("aapl", period="weekly")
    assert result["ok"] is False
    assert "period" in result["error"]


async def test_dividends_envelope(use_source):
    use_source(FakeSource())
    result = await app_module.dividends("KO")
    assert result["ok"] is True
    assert result["data"]["growth_streak_years"] == 10


async def test_tool_surfaces_error_as_envelope(use_source):
    use_source(BrokenSource())
    result = await app_module.company_snapshot("aapl")
    assert result["ok"] is False
    assert "data source down" in result["error"]


def test_parse_as_of_handles_blank_and_value():
    assert app_module._parse_as_of(None) is None
    assert app_module._parse_as_of("  ") is None
    assert app_module._parse_as_of("2024-03-02") == date(2024, 3, 2)
