from datetime import date
from decimal import Decimal

import pytest

from scout.config import Settings, get_settings
from scout.domain.models import (
    CompanySnapshot,
    DividendHistory,
    Filing,
    FilingsList,
    Fundamentals,
    Period,
    PriceBar,
    PriceHistory,
)
from scout.server import app as app_module
from scout.server.services import Services


class FakeSource:
    async def get_snapshot(self, symbol, as_of=None):
        return CompanySnapshot(symbol=symbol.upper(), price=Decimal("100"), as_of=as_of)

    async def get_fundamentals(self, symbol, period=Period.ANNUAL, as_of=None):
        return Fundamentals(symbol=symbol.upper(), period=period, revenue=Decimal("1000"))

    async def get_dividends(self, symbol, as_of=None):
        return DividendHistory(symbol=symbol.upper(), growth_streak_years=10)

    async def get_price_history(self, symbol, range="6mo", interval="1d", as_of=None):
        def bar(day, close, high, low):
            return PriceBar(
                date=date(2024, 1, day),
                close=Decimal(close),
                high=Decimal(high),
                low=Decimal(low),
            )

        bars = [bar(1, "100", "101", "99"), bar(2, "102", "103", "101")]
        return PriceHistory(symbol=symbol.upper(), interval=interval, bars=bars, as_of=as_of)


class BrokenSource(FakeSource):
    async def get_snapshot(self, symbol, as_of=None):
        raise RuntimeError("data source down")


class FakeFilings:
    async def get_filings(self, symbol, form_type=None, limit=20, as_of=None):
        return FilingsList(
            symbol=symbol.upper(),
            cik="0000320193",
            filings=[Filing(form="10-K", filing_date=date(2024, 11, 1), accession="x")],
        )


@pytest.fixture
def use_source():
    previous = app_module._services

    def _install(source, filings=None, settings=None):
        app_module._services = Services(
            settings=settings or get_settings(), market_data=source, filings=filings
        )

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


async def test_company_dossier_envelope(use_source):
    use_source(FakeSource())
    result = await app_module.company_dossier("aapl")
    assert result["ok"] is True
    assert result["data"]["symbol"] == "AAPL"
    assert result["data"]["snapshot"]["price"] == "100"
    assert result["data"]["fundamentals"] is not None
    assert result["data"]["notes"] == []


async def test_company_dossier_rejects_bad_depth(use_source):
    use_source(FakeSource())
    result = await app_module.company_dossier("aapl", depth="everything")
    assert result["ok"] is False
    assert "depth" in result["error"]


async def test_tool_surfaces_error_as_envelope(use_source):
    use_source(BrokenSource())
    result = await app_module.company_snapshot("aapl")
    assert result["ok"] is False
    assert "data source down" in result["error"]


async def test_price_history_tool(use_source):
    use_source(FakeSource())
    result = await app_module.price_history("aapl")
    assert result["ok"] is True
    assert len(result["data"]["bars"]) == 2
    assert result["data"]["bars"][1]["close"] == "102"


async def test_technicals_tool(use_source):
    use_source(FakeSource())
    result = await app_module.technicals("aapl")
    assert result["ok"] is True
    assert result["data"]["last_price"] == "102.0000"
    assert result["data"]["bars_used"] == 2
    assert result["data"]["sma_50"] is None  # only 2 bars


async def test_filings_requires_user_agent(use_source):
    use_source(FakeSource(), filings=FakeFilings())  # default settings → blank UA
    result = await app_module.filings("AAPL")
    assert result["ok"] is False
    assert "SCOUT_SEC_USER_AGENT" in result["error"]


async def test_filings_returns_data_when_configured(use_source):
    use_source(
        FakeSource(),
        filings=FakeFilings(),
        settings=Settings(sec_user_agent="Scout Test test@example.com"),
    )
    result = await app_module.filings("aapl", form_type="10-K")
    assert result["ok"] is True
    assert result["data"]["cik"] == "0000320193"
    assert result["data"]["filings"][0]["form"] == "10-K"


def test_parse_as_of_handles_blank_and_value():
    assert app_module._parse_as_of(None) is None
    assert app_module._parse_as_of("  ") is None
    assert app_module._parse_as_of("2024-03-02") == date(2024, 3, 2)
