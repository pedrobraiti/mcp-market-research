"""Composition root: assembles the concrete adapters from the Settings.

The rest of the code depends only on the ports (``MarketDataSource``). Swapping yfinance
for another source — or fanning several sources into one dossier — happens here.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..adapters.yfinance import YFinanceMarketData
from ..config import Settings, get_settings
from ..domain.ports import MarketDataSource


@dataclass
class Services:
    settings: Settings
    market_data: MarketDataSource


def build_services(settings: Settings | None = None) -> Services:
    settings = settings or get_settings()
    return Services(settings=settings, market_data=YFinanceMarketData())
