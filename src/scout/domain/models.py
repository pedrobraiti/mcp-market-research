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


class MoverRow(BaseModel):
    symbol: str
    name: str | None = None
    price: Decimal | None = None
    change_percent: Decimal | None = None
    volume: int | None = None


class MoversList(BaseModel):
    """Market-wide top gainers / losers / most-active — discovery without a symbol in hand."""

    category: str
    movers: list[MoverRow] = []


class SymbolMatch(BaseModel):
    symbol: str
    name: str | None = None
    exchange: str | None = None
    type: str | None = None


class SymbolSearch(BaseModel):
    """Tickers matching a free-text query (company name, partial ticker)."""

    query: str
    matches: list[SymbolMatch] = []


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
    next_ex_dividend: date | None = None
    payments: list[DividendPayment] = []
    as_of: date | None = None


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


class ClassificationItem(BaseModel):
    symbol: str
    name: str | None = None
    sector: str | None = None
    industry: str | None = None
    market_cap: Decimal | None = None
    note: str | None = None


class Classification(BaseModel):
    """Sector/industry/cap per symbol, in one call — for the agent to aggregate exposure."""

    items: list[ClassificationItem] = []
    as_of: date | None = None


class DigestNewsItem(BaseModel):
    symbol: str
    title: str | None = None
    publisher: str | None = None
    published: datetime | None = None
    url: str | None = None


class NewsDigest(BaseModel):
    """Material headlines across several symbols in one call, newest first."""

    symbols: list[str]
    items: list[DigestNewsItem] = []
    notes: list[str] = []


class CalendarEvent(BaseModel):
    symbol: str
    type: str  # "earnings" | "ex_dividend"
    date: date


class MarketCalendar(BaseModel):
    """Upcoming earnings and ex-dividend dates across several symbols, sorted by date."""

    symbols: list[str]
    events: list[CalendarEvent] = []
    notes: list[str] = []


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


class CompanyDossier(BaseModel):
    """A consolidated, single-call portrait that fans several reads out in parallel.

    The flagship "research many things about a company at once" tool: snapshot, fundamentals,
    dividends, technicals, earnings, analyst view and news gathered concurrently and returned
    together. ``notes`` carries any partial failure so the dossier degrades gracefully.
    """

    symbol: str
    as_of: date | None = None
    snapshot: CompanySnapshot | None = None
    fundamentals: Fundamentals | None = None
    dividends: DividendHistory | None = None
    technicals: Technicals | None = None
    earnings: EarningsInfo | None = None
    analyst: AnalystView | None = None
    news: NewsList | None = None
    notes: list[str] = []


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


class QualityMetrics(BaseModel):
    """Derived quality/return ratios — ROE/ROA, margins and growth/CAGR. Raw numbers, no rating."""

    symbol: str
    roe: Decimal | None = None
    roa: Decimal | None = None
    gross_margin: Decimal | None = None
    operating_margin: Decimal | None = None
    net_margin: Decimal | None = None
    revenue_growth_yoy: Decimal | None = None
    earnings_growth_yoy: Decimal | None = None
    revenue_cagr: Decimal | None = None
    net_income_cagr: Decimal | None = None
    cagr_years: int | None = None
    as_of: date | None = None


class RelativeStrengthRow(BaseModel):
    symbol: str
    return_percent: Decimal | None = None
    excess_vs_benchmark: Decimal | None = None
    note: str | None = None


class RelativeStrength(BaseModel):
    """Each symbol's total return over a period vs a benchmark — momentum/leadership, as data."""

    benchmark: str
    period: str
    benchmark_return_percent: Decimal | None = None
    rows: list[RelativeStrengthRow] = []
    notes: list[str] = []


class SectorReturn(BaseModel):
    sector: str
    etf: str
    return_percent: Decimal | None = None


class SectorPerformance(BaseModel):
    """Total return of each US sector (via its SPDR ETF) over a period — rotation, as data."""

    period: str
    sectors: list[SectorReturn] = []
    notes: list[str] = []


class EtfHolding(BaseModel):
    symbol: str
    name: str | None = None
    weight: Decimal | None = None


class EtfHoldings(BaseModel):
    """An ETF's declared basket — top holdings and sector weights, straight from the issuer."""

    symbol: str
    top_holdings: list[EtfHolding] = []
    sector_weights: dict[str, Decimal] = {}
    note: str | None = None


class InsiderTransaction(BaseModel):
    transaction_date: date | None = None
    insider: str | None = None
    position: str | None = None
    transaction: str | None = None
    shares: Decimal | None = None
    value: Decimal | None = None


class InstitutionalHolder(BaseModel):
    holder: str | None = None
    shares: Decimal | None = None
    pct_out: Decimal | None = None
    value: Decimal | None = None


class Ownership(BaseModel):
    """Who owns the stock: insider/institution percentages, top institutions, insider trades.

    Public-record data (13F / Form 4), reported as facts — a skin-in-the-game signal the agent
    interprets. No verdict.
    """

    symbol: str
    insider_percent: Decimal | None = None
    institution_percent: Decimal | None = None
    institutional_holders: list[InstitutionalHolder] = []
    insider_transactions: list[InsiderTransaction] = []


class OptionsVolatility(BaseModel):
    """Implied volatility and the options-implied expected move to an expiry. Raw data."""

    symbol: str
    expiry: date | None = None
    days_to_expiry: int | None = None
    current_price: Decimal | None = None
    atm_strike: Decimal | None = None
    atm_iv: Decimal | None = Field(
        default=None, description="ATM implied vol, annualized fraction."
    )
    expected_move_percent: Decimal | None = Field(
        default=None, description="1-sigma move to expiry = IV * sqrt(days/365)."
    )
    expected_move_amount: Decimal | None = None
    expected_move_low: Decimal | None = None
    expected_move_high: Decimal | None = None
    note: str | None = None


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
