"""Domain ports (interfaces) — contracts that concrete adapters implement.

Async ``Protocol``s: a data source (yfinance today; SEC EDGAR, FRED, a paid provider
tomorrow) must satisfy these without explicit inheritance. Every method takes an optional
``as_of`` so the same call can read the present or a past snapshot — the key to keeping
Scout stateless while still serving "what changed since" questions.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

from .models import (
    AnalystView,
    CompanySnapshot,
    DividendHistory,
    EarningsInfo,
    ExtractedPage,
    FilingsList,
    Fundamentals,
    MacroSnapshot,
    NewsList,
    Period,
    PriceHistory,
    SecFinancials,
    SymbolSearch,
)


@runtime_checkable
class MarketDataSource(Protocol):
    """Reads of company-level market and fundamental data."""

    async def get_snapshot(
        self, symbol: str, as_of: date | None = None
    ) -> CompanySnapshot | None:
        """Price, day move and key multiples. ``None`` if the symbol can't be resolved."""
        ...

    async def get_fundamentals(
        self, symbol: str, period: Period = Period.ANNUAL, as_of: date | None = None
    ) -> Fundamentals | None:
        """Income/balance/cash-flow figures for the latest period at or before ``as_of``."""
        ...

    async def get_dividends(
        self, symbol: str, as_of: date | None = None
    ) -> DividendHistory | None:
        """Dividend history, trailing yield, growth streak and cut flag up to ``as_of``."""
        ...

    async def get_price_history(
        self,
        symbol: str,
        range: str = "6mo",
        interval: str = "1d",
        as_of: date | None = None,
    ) -> PriceHistory | None:
        """OHLCV bars over ``range`` at ``interval``, truncated at/before ``as_of``."""
        ...

    async def get_news(self, symbol: str, limit: int = 10) -> NewsList | None:
        """Recent news headlines (title, publisher, date, url) for a symbol."""
        ...

    async def get_earnings(self, symbol: str, as_of: date | None = None) -> EarningsInfo | None:
        """Upcoming earnings date and history (estimate / actual / surprise)."""
        ...

    async def get_analyst_view(self, symbol: str) -> AnalystView | None:
        """Sell-side consensus rating and price targets (third-party opinion, as data)."""
        ...

    async def search_symbols(self, query: str, limit: int = 10) -> SymbolSearch:
        """Resolve a free-text query (company name / partial ticker) to matching symbols."""
        ...


@runtime_checkable
class FilingsSource(Protocol):
    """Reads of regulatory filings (SEC EDGAR today)."""

    async def get_filings(
        self,
        symbol: str,
        form_type: str | None = None,
        limit: int = 20,
        as_of: date | None = None,
    ) -> FilingsList | None:
        """Recent filings, optionally restricted to ``form_type`` and dated at/before ``as_of``."""
        ...


@runtime_checkable
class FinancialsSource(Protocol):
    """Reads of authoritative reported financials (SEC EDGAR XBRL today)."""

    async def get_financials(self, symbol: str, as_of: date | None = None) -> SecFinancials | None:
        """Latest annual reported figures (with provenance) at or before ``as_of``."""
        ...


@runtime_checkable
class MacroSource(Protocol):
    """Reads of macro indicators (FRED today)."""

    async def get_macro_context(self, as_of: date | None = None) -> MacroSnapshot:
        """Latest value of each key macro series, at or before ``as_of``."""
        ...


@runtime_checkable
class ContentExtractor(Protocol):
    """Fetches a web page and returns its main content as clean markdown."""

    async def extract(self, url: str) -> ExtractedPage:
        """Fetch ``url`` and extract the main content. Always returns a result (with
        ``fetched_ok=False`` and a note on a block/error), never raises for the agent."""
        ...
