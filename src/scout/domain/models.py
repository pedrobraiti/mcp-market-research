"""Domain models — agnostic to the concrete data source.

Monetary and ratio values use ``Decimal`` to avoid floating-point noise (mirrors the
mcp-ibkr-agent convention). Every research model carries an optional ``as_of`` date: when
``None`` the data is the latest/real-time read; when set, it is (best-effort) the snapshot
as of that date. ``as_of`` is what lets the calling agent compose two stateless reads into
a "what changed since I bought?" diff — Scout never stores the date, it receives it.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class Period(StrEnum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"


class CompanySnapshot(BaseModel):
    """A light, single-call portrait: price, day move and the key multiples."""

    symbol: str
    name: str | None = None
    currency: str = "USD"
    price: Decimal | None = None
    previous_close: Decimal | None = None
    change: Decimal | None = None
    change_percent: Decimal | None = None
    market_cap: Decimal | None = None
    pe_ratio: Decimal | None = None
    forward_pe: Decimal | None = None
    dividend_yield: Decimal | None = Field(
        default=None, description="As reported by the source (typically a fraction, e.g. 0.0044)."
    )
    fifty_two_week_high: Decimal | None = None
    fifty_two_week_low: Decimal | None = None
    sector: str | None = None
    industry: str | None = None
    as_of: date | None = None


class Fundamentals(BaseModel):
    """Core income-statement / balance-sheet / cash-flow figures plus derived margins."""

    symbol: str
    period: Period
    fiscal_period_end: date | None = None
    revenue: Decimal | None = None
    gross_profit: Decimal | None = None
    operating_income: Decimal | None = None
    net_income: Decimal | None = None
    gross_margin: Decimal | None = None
    operating_margin: Decimal | None = None
    net_margin: Decimal | None = None
    total_debt: Decimal | None = None
    total_cash: Decimal | None = None
    free_cash_flow: Decimal | None = None
    as_of: date | None = None


class DividendPayment(BaseModel):
    ex_date: date
    amount: Decimal


class DividendHistory(BaseModel):
    """The income story: payment history, trailing yield, growth streak and any cut.

    Pure data — no judgment about whether the dividend is "safe". The agent reads the
    streak/cut/yield and concludes.
    """

    symbol: str
    currency: str = "USD"
    trailing_12m: Decimal | None = Field(
        default=None, description="Sum of dividends paid in the trailing 12 months."
    )
    trailing_yield: Decimal | None = Field(
        default=None, description="trailing_12m / price, if a price is available."
    )
    growth_streak_years: int | None = Field(
        default=None, description="Consecutive full calendar years of non-decreasing dividends."
    )
    had_cut: bool | None = Field(
        default=None, description="Whether any year-over-year cut is present in the history."
    )
    payments: list[DividendPayment] = []
    as_of: date | None = None


class CompanyDossier(BaseModel):
    """A consolidated, single-call portrait that fans several reads out in parallel.

    The flagship "research many things about a company at once" tool: snapshot + fundamentals
    + dividends gathered concurrently and returned together. ``notes`` carries any partial
    failure (one source down) so the dossier degrades gracefully instead of failing whole.
    """

    symbol: str
    as_of: date | None = None
    snapshot: CompanySnapshot | None = None
    fundamentals: Fundamentals | None = None
    dividends: DividendHistory | None = None
    notes: list[str] = []


class ComparisonRow(BaseModel):
    symbol: str
    name: str | None = None
    price: Decimal | None = None
    market_cap: Decimal | None = None
    pe_ratio: Decimal | None = None
    forward_pe: Decimal | None = None
    dividend_yield: Decimal | None = None
    revenue: Decimal | None = None
    net_margin: Decimal | None = None
    sector: str | None = None
    note: str | None = None


class Comparison(BaseModel):
    """Several symbols side by side — a parallel gather of snapshot + fundamentals per name."""

    symbols: list[str]
    as_of: date | None = None
    rows: list[ComparisonRow] = []


class CorrelationMatrix(BaseModel):
    """Pairwise return correlation between symbols — diversification you can't see per-symbol."""

    symbols: list[str]
    period: str
    days: int | None = None
    matrix: dict[str, dict[str, float | None]] = {}
    notes: list[str] = []


class Filing(BaseModel):
    """A single SEC filing (10-K, 10-Q, 8-K, ...) with a link to the primary document."""

    form: str
    filing_date: date
    report_date: date | None = None
    accession: str
    primary_document: str | None = None
    description: str | None = None
    url: str | None = None


class FilingsList(BaseModel):
    """Recent SEC EDGAR filings for a company — authoritative, straight from the source."""

    symbol: str
    cik: str | None = None
    name: str | None = None
    filings: list[Filing] = []


class PriceBar(BaseModel):
    date: date
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None
    volume: int | None = None


class PriceHistory(BaseModel):
    """OHLCV bars for a symbol over a range/interval."""

    symbol: str
    interval: str
    bars: list[PriceBar] = []
    as_of: date | None = None


class Technicals(BaseModel):
    """Computed technical indicators — raw numbers, no trend verdict (that's the agent's call)."""

    symbol: str
    as_of: date | None = None
    last_price: Decimal | None = None
    sma_50: Decimal | None = None
    sma_200: Decimal | None = None
    ema_20: Decimal | None = None
    rsi_14: Decimal | None = None
    macd: Decimal | None = None
    macd_signal: Decimal | None = None
    macd_histogram: Decimal | None = None
    atr_14: Decimal | None = None
    week52_high: Decimal | None = None
    week52_low: Decimal | None = None
    bars_used: int | None = None


class MacroIndicator(BaseModel):
    series_id: str
    name: str
    value: Decimal | None = None
    observation_date: date | None = None


class MacroSnapshot(BaseModel):
    """A snapshot of key macro indicators (rates, spread, unemployment, CPI, VIX)."""

    indicators: list[MacroIndicator] = []
    as_of: date | None = None


class SecFinancialLine(BaseModel):
    """One reported financial figure from SEC XBRL, with full provenance."""

    concept: str
    tag: str | None = None
    value: Decimal | None = None
    unit: str | None = None
    period_end: date | None = None
    fiscal_year: int | None = None
    form: str | None = None
    filed: date | None = None


class SecFinancials(BaseModel):
    """Authoritative annual financials from SEC EDGAR XBRL — to cross-check other sources.

    Every line carries which tag/filing/period it came from, so a figure can be audited
    against the primary document. Raw reported numbers, no derived verdict.
    """

    symbol: str
    cik: str | None = None
    fiscal_year: int | None = None
    period_end: date | None = None
    lines: list[SecFinancialLine] = []
    as_of: date | None = None


class NewsItem(BaseModel):
    title: str | None = None
    publisher: str | None = None
    published: datetime | None = None
    url: str | None = None
    summary: str | None = None


class NewsList(BaseModel):
    """Recent headlines for a symbol — links the agent can then `extract` and read in full."""

    symbol: str
    items: list[NewsItem] = []


class EarningsEvent(BaseModel):
    event_date: date | None = None
    eps_estimate: Decimal | None = None
    eps_reported: Decimal | None = None
    surprise_percent: Decimal | None = None
    is_future: bool | None = None


class EarningsInfo(BaseModel):
    """Earnings calendar and history: upcoming dates plus past estimate/actual/surprise."""

    symbol: str
    next_earnings_date: date | None = None
    events: list[EarningsEvent] = []


class AnalystView(BaseModel):
    """What sell-side analysts say — third-party opinion reported as data, NOT Scout's verdict."""

    symbol: str
    recommendation_key: str | None = None
    recommendation_mean: Decimal | None = Field(
        default=None, description="Consensus 1=strong buy … 5=sell (as reported)."
    )
    number_of_analysts: int | None = None
    current_price: Decimal | None = None
    target_mean: Decimal | None = None
    target_median: Decimal | None = None
    target_high: Decimal | None = None
    target_low: Decimal | None = None


class ExtractedPage(BaseModel):
    """A web page fetched and reduced to clean, token-efficient markdown.

    A pure capture sense for the agent's own research: it picks the URL, this returns the main
    content. It does NOT judge or summarize. ``fetched_ok=False`` (with a note) honestly reports
    a paywall/anti-bot block rather than pretending — the kind of gap the benchmark exposed.
    """

    url: str
    fetched_ok: bool
    status_code: int | None = None
    title: str | None = None
    markdown: str | None = None
    char_count: int | None = None
    note: str | None = None
