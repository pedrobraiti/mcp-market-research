"""Composition root: assembles the concrete adapters from the Settings.

The rest of the code depends only on the ports (``MarketDataSource``, ``FilingsSource``).
Swapping a source — or fanning several into one dossier — happens here.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..adapters.apewisdom import ApeWisdomBuzz
from ..adapters.fred import FredMacro
from ..adapters.gdelt import GdeltNewsSearch
from ..adapters.price_fallback import PriceFallbackMarketData
from ..adapters.sec import SecEdgar
from ..adapters.stooq import StooqPrices
from ..adapters.web import WebExtractor
from ..adapters.yfinance import YFinanceMarketData
from ..config import Settings, get_settings
from ..domain.ports import (
    ContentExtractor,
    FilingsSource,
    FinancialsSource,
    MacroSource,
    MarketDataSource,
    NewsSearchSource,
    RetailBuzzSource,
)


@dataclass
class Services:
    settings: Settings
    market_data: MarketDataSource
    filings: FilingsSource | None = None
    financials: FinancialsSource | None = None
    extractor: ContentExtractor | None = None
    macro: MacroSource | None = None
    news_search: NewsSearchSource | None = None
    retail_buzz: RetailBuzzSource | None = None


def build_services(settings: Settings | None = None) -> Services:
    settings = settings or get_settings()
    timeout = settings.request_timeout_seconds
    sec = SecEdgar(settings.sec_user_agent, timeout=timeout)  # one instance: filings + financials
    market_data = PriceFallbackMarketData(YFinanceMarketData(), StooqPrices(timeout=timeout))
    return Services(
        settings=settings,
        market_data=market_data,
        filings=sec,
        financials=sec,
        extractor=WebExtractor(settings.web_user_agent, timeout=timeout),
        macro=FredMacro(timeout=timeout),
        news_search=GdeltNewsSearch(timeout=timeout),
        retail_buzz=ApeWisdomBuzz(timeout=timeout),
    )
