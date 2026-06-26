"""Composition root: assembles the concrete adapters from the Settings.

The rest of the code depends only on the ports (``MarketDataSource``, ``FilingsSource``).
Swapping a source — or fanning several into one dossier — happens here.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..adapters.fred import FredMacro
from ..adapters.sec import SecEdgar
from ..adapters.web import WebExtractor
from ..adapters.yfinance import YFinanceMarketData
from ..config import Settings, get_settings
from ..domain.ports import (
    ContentExtractor,
    FilingsSource,
    FinancialsSource,
    MacroSource,
    MarketDataSource,
)


@dataclass
class Services:
    settings: Settings
    market_data: MarketDataSource
    filings: FilingsSource | None = None
    financials: FinancialsSource | None = None
    extractor: ContentExtractor | None = None
    macro: MacroSource | None = None


def build_services(settings: Settings | None = None) -> Services:
    settings = settings or get_settings()
    timeout = settings.request_timeout_seconds
    sec = SecEdgar(settings.sec_user_agent, timeout=timeout)  # one instance: filings + financials
    return Services(
        settings=settings,
        market_data=YFinanceMarketData(),
        filings=sec,
        financials=sec,
        extractor=WebExtractor(settings.web_user_agent, timeout=timeout),
        macro=FredMacro(timeout=timeout),
    )
