"""Composition root: assembles the concrete adapters from the Settings.

The rest of the code depends only on the ports (``MarketDataSource``, ``FilingsSource``).
Swapping a source — or fanning several into one dossier — happens here.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..adapters.sec import SecEdgarFilings
from ..adapters.web import WebExtractor
from ..adapters.yfinance import YFinanceMarketData
from ..config import Settings, get_settings
from ..domain.ports import ContentExtractor, FilingsSource, MarketDataSource


@dataclass
class Services:
    settings: Settings
    market_data: MarketDataSource
    filings: FilingsSource | None = None
    extractor: ContentExtractor | None = None


def build_services(settings: Settings | None = None) -> Services:
    settings = settings or get_settings()
    timeout = settings.request_timeout_seconds
    return Services(
        settings=settings,
        market_data=YFinanceMarketData(),
        filings=SecEdgarFilings(settings.sec_user_agent, timeout=timeout),
        extractor=WebExtractor(settings.web_user_agent, timeout=timeout),
    )
