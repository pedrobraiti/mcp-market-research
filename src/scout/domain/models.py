"""Domain models — agnostic to the concrete data source.

Monetary and ratio values use ``Decimal`` to avoid floating-point noise (mirrors the
agentic-trading-mcp convention). Every research model carries an optional ``as_of`` date: when
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


class StockSplit(BaseModel):
    """A single executed stock split. ``ratio`` is shares-out per old share (e.g. 10 for 10:1)."""

    date: date
    ratio: Decimal | None = Field(
        default=None, description="New shares per old share — 10 means a 10:1 split, 0.1 a 1:10."
    )


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
    recent_splits: list[StockSplit] = Field(
        default_factory=list,
        description=(
            "Recent stock splits (newest first), so a split-adjusted price isn't mistaken for "
            "'wrong' against pre-split memory. Empty when none are known. Price and 52-week range "
            "are already split-adjusted by the source."
        ),
    )
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
    status: str | None = Field(
        default=None,
        description=(
            "Set when the series couldn't be fetched (e.g. 'unavailable: rate_limited' / "
            "'unavailable: timeout') — distinct from a genuine null value. None means fetched OK."
        ),
    )


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


class WorldBankIndicator(BaseModel):
    code: str
    name: str | None = None
    value: Decimal | None = None
    year: int | None = None
    country: str | None = None


class WorldBankData(BaseModel):
    """Key macro indicators for a country from the World Bank (global, official, keyless)."""

    country: str
    indicators: list[WorldBankIndicator] = []


class TreasuryFigure(BaseModel):
    name: str
    value: Decimal | None = None
    unit: str | None = None
    record_date: date | None = None


class TreasuryData(BaseModel):
    """Official US Treasury fiscal data (debt, average interest rates) — keyless, authoritative."""

    figures: list[TreasuryFigure] = []


class PageviewDay(BaseModel):
    day: date
    views: int | None = None


class WikipediaAttention(BaseModel):
    """Daily Wikipedia pageviews for an article — an official, stable attention proxy."""

    article: str
    days: int
    total_views: int | None = None
    items: list[PageviewDay] = []
    note: str | None = None


class RetailBuzzItem(BaseModel):
    symbol: str
    name: str | None = None
    rank: int | None = None
    rank_24h_ago: int | None = None
    mentions: int | None = None
    mentions_24h_ago: int | None = None
    upvotes: int | None = None


class RetailBuzz(BaseModel):
    """Reddit (WSB/stocks) mention buzz — a retail-attention signal, not a sentiment score."""

    symbol: str | None = None
    items: list[RetailBuzzItem] = []
    note: str | None = None


class WebNewsItem(BaseModel):
    title: str | None = None
    domain: str | None = None
    url: str | None = None
    published: datetime | None = None
    language: str | None = None
    country: str | None = None


class WebNewsSearch(BaseModel):
    """Free-text news/event search across global media (GDELT) — by theme or company name."""

    query: str
    items: list[WebNewsItem] = []
    source_status: str | None = Field(
        default=None,
        description=(
            "Set when the source couldn't be reached (e.g. 'unavailable: rate_limited') — so an "
            "empty result from a 429/timeout is distinguishable from a genuine 'no matches'."
        ),
    )


class FilingSearchHit(BaseModel):
    company: str | None = None
    ticker: str | None = None
    cik: str | None = None
    form: str | None = None
    filing_date: date | None = None
    url: str | None = None


class FilingSearch(BaseModel):
    """Companies/filings matching a full-text query across all EDGAR filings (thesis → names)."""

    query: str
    total: int | None = None
    hits: list[FilingSearchHit] = []


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


# --- Crypto models (spot, BASE/QUOTE) -----------------------------------------------------
# Mirror the equities models but for crypto spot pairs. Symbols use the CCXT unified format
# ``BASE/QUOTE`` (e.g. ``BTC/USDT``) so a researched asset maps straight to a tradable pair on
# the execution side. Data only — never a verdict (same constitution as the rest of Scout).


class CryptoQuote(BaseModel):
    """A live spot quote for a crypto pair — last/bid/ask and the 24h move."""

    symbol: str  # CCXT unified pair, e.g. "BTC/USDT"
    base: str  # e.g. "BTC"
    quote: str  # e.g. "USDT"
    exchange: str
    last: Decimal | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    high_24h: Decimal | None = None
    low_24h: Decimal | None = None
    change_percent_24h: Decimal | None = None
    base_volume_24h: Decimal | None = None
    quote_volume_24h: Decimal | None = None
    timestamp: datetime | None = None


class CryptoBar(BaseModel):
    """One OHLCV candle. ``timestamp`` keeps intraday resolution (the date-keyed PriceBar can't)."""

    timestamp: datetime
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None
    volume: Decimal | None = None  # base-asset volume (fractional in crypto)


class CryptoPriceHistory(BaseModel):
    """OHLCV candles for a crypto pair over a timeframe."""

    symbol: str  # CCXT unified pair, e.g. "BTC/USDT"
    base: str
    quote: str
    exchange: str
    timeframe: str  # CCXT timeframe, e.g. "1d", "1h", "5m"
    bars: list[CryptoBar] = []
    as_of: date | None = None


class CryptoAssetProfile(BaseModel):
    """Supply, market cap, rank and ATH for a crypto asset (the 'fundamentals' of crypto).

    Sourced from an aggregator (Coinpaprika) keyed by the asset, not a single exchange — raw
    facts (circulating/total/max supply, market cap, rank), not a verdict on value.
    """

    base: str  # e.g. "BTC"
    name: str | None = None
    source_id: str | None = None  # the aggregator's id, e.g. "btc-bitcoin"
    rank: int | None = None
    price_usd: Decimal | None = None
    market_cap_usd: Decimal | None = None
    volume_24h_usd: Decimal | None = None
    circulating_supply: Decimal | None = None
    total_supply: Decimal | None = None
    max_supply: Decimal | None = None
    ath_price_usd: Decimal | None = None
    ath_date: date | None = None
    percent_from_ath: Decimal | None = None


class FearGreedPoint(BaseModel):
    value: int | None = None
    classification: str | None = None
    observation_date: date | None = None


class CryptoFearGreed(BaseModel):
    """The Crypto Fear & Greed Index (alternative.me) — a market-wide sentiment gauge 0-100.

    Market-level, not per-coin. Raw index + history; the agent reads the level, no buy/sell call.
    """

    value: int | None = None
    classification: str | None = None
    observation_date: date | None = None
    history: list[FearGreedPoint] = []


# --- Crypto Tier 2: on-chain, derivatives, implied volatility -----------------------------


class OnChainMetric(BaseModel):
    name: str
    value: Decimal | None = None
    unit: str | None = None


class CryptoOnChain(BaseModel):
    """Network-health metrics for a chain (BTC fees/hashrate, ETH gas/addresses, …).

    Heterogeneous across chains, so metrics are a labelled list. Raw on-chain facts, not a verdict.
    """

    asset: str
    source: str
    metrics: list[OnChainMetric] = []
    note: str | None = None


class DerivativesVenue(BaseModel):
    exchange: str
    symbol: str | None = None
    funding_rate: Decimal | None = None
    next_funding_time: datetime | None = None
    mark_price: Decimal | None = None
    open_interest: Decimal | None = None
    open_interest_value: Decimal | None = None


class CryptoDerivatives(BaseModel):
    """Perp funding rate and open interest across exchanges — positioning CONTEXT, never executed.

    The execution side is spot-only; this is a sentiment/positioning read (funding sign & size, OI
    trend). Raw numbers per venue; the agent interprets crowding.
    """

    base: str
    venues: list[DerivativesVenue] = []
    note: str | None = None


class VolPoint(BaseModel):
    timestamp: datetime
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None


class CryptoImpliedVol(BaseModel):
    """The Deribit DVOL index ('crypto VIX') — current value plus recent history.

    Options-implied volatility for BTC/ETH: how much swing the options market is pricing. Raw
    index, useful to size a stop or gauge the vol regime — not a trade call.
    """

    asset: str
    dvol_current: Decimal | None = None
    history: list[VolPoint] = []
    note: str | None = None


# --- Crypto Tier 3: DeFi, stablecoins, yields, macro, sectors ------------------------------


class DefiTvlItem(BaseModel):
    name: str
    tvl_usd: Decimal | None = None


class DefiOverview(BaseModel):
    """DeFi total value locked — by chain (no slug) or one protocol's breakdown (with slug)."""

    scope: str  # "chains" or a protocol slug
    total_tvl_usd: Decimal | None = None
    items: list[DefiTvlItem] = []


class StablecoinItem(BaseModel):
    symbol: str | None = None
    name: str | None = None
    peg_type: str | None = None
    peg_mechanism: str | None = None
    price: Decimal | None = None
    peg_deviation: Decimal | None = None  # price - 1.0 for USD-pegged
    circulating_usd: Decimal | None = None


class StablecoinSupply(BaseModel):
    """Stablecoin circulation and peg status (DefiLlama) — liquidity & systemic-risk read."""

    total_circulating_usd: Decimal | None = None
    items: list[StablecoinItem] = []


class YieldPool(BaseModel):
    project: str | None = None
    chain: str | None = None
    symbol: str | None = None
    tvl_usd: Decimal | None = None
    apy: Decimal | None = None
    apy_base: Decimal | None = None
    apy_reward: Decimal | None = None


class DefiYields(BaseModel):
    """DeFi yield/APY pools (DefiLlama), filterable by chain/project/min TVL — context only."""

    pools: list[YieldPool] = []


class CryptoMacro(BaseModel):
    """Crypto-wide macro snapshot (CoinGecko): total market cap, dominance, DeFi share."""

    total_market_cap_usd: Decimal | None = None
    total_volume_24h_usd: Decimal | None = None
    market_cap_change_percent_24h: Decimal | None = None
    btc_dominance: Decimal | None = None
    eth_dominance: Decimal | None = None
    defi_market_cap_usd: Decimal | None = None
    defi_dominance: Decimal | None = None
    active_cryptocurrencies: int | None = None


class CryptoCategory(BaseModel):
    name: str
    market_cap_usd: Decimal | None = None
    market_cap_change_24h: Decimal | None = None
    volume_24h_usd: Decimal | None = None
    top_3_coins: list[str] = []


class CryptoSectors(BaseModel):
    """Per-category (sector) performance for crypto (CoinGecko) — where money rotated."""

    categories: list[CryptoCategory] = []


# --- Crypto parity / discovery -------------------------------------------------------------


class CryptoMover(BaseModel):
    symbol: str
    base: str | None = None
    last: Decimal | None = None
    change_percent_24h: Decimal | None = None
    quote_volume_24h: Decimal | None = None


class CryptoMoversList(BaseModel):
    """Market-wide top gainers / losers / most-active crypto pairs on the configured exchange."""

    category: str
    exchange: str
    quote: str
    movers: list[CryptoMover] = []


class OrderBookLevel(BaseModel):
    price: Decimal | None = None
    amount: Decimal | None = None


class CryptoOrderBook(BaseModel):
    """Top-of-book and aggregated depth for a pair — a pre-trade liquidity/slippage read."""

    symbol: str
    exchange: str
    bid: Decimal | None = None
    ask: Decimal | None = None
    spread: Decimal | None = None
    spread_percent: Decimal | None = None
    bid_depth_base: Decimal | None = None
    ask_depth_base: Decimal | None = None
    levels: int | None = None
    top_bids: list[OrderBookLevel] = []
    top_asks: list[OrderBookLevel] = []


class CryptoComparisonRow(BaseModel):
    symbol: str
    base: str
    last: Decimal | None = None
    change_percent_24h: Decimal | None = None
    market_cap_usd: Decimal | None = None
    rank: int | None = None
    circulating_supply: Decimal | None = None
    note: str | None = None


class CryptoComparison(BaseModel):
    """Several crypto assets side by side (quote + profile), in one call."""

    items: list[CryptoComparisonRow] = []


class CryptoCorrelationPair(BaseModel):
    a: str
    b: str
    correlation: Decimal | None = None


class CryptoCorrelation(BaseModel):
    """Pairwise return correlation between crypto pairs — real diversification."""

    timeframe: str
    bars_used: int | None = None
    pairs: list[CryptoCorrelationPair] = []
    note: str | None = None


class CryptoRelStrengthRow(BaseModel):
    symbol: str
    return_percent: Decimal | None = None
    excess_vs_benchmark: Decimal | None = None


class CryptoRelativeStrength(BaseModel):
    """Each pair's return over a window vs a benchmark (default BTC) — leadership read."""

    benchmark: str
    timeframe: str
    rows: list[CryptoRelStrengthRow] = []
    notes: list[str] = []


class CryptoSymbolMatch(BaseModel):
    base: str
    name: str | None = None
    source_id: str | None = None
    rank: int | None = None


class CryptoSymbolSearch(BaseModel):
    """Crypto assets matching a free-text query (name / partial symbol)."""

    query: str
    matches: list[CryptoSymbolMatch] = []


class CryptoDossier(BaseModel):
    """Consolidated one-call crypto portrait — fans several reads out in parallel.

    The crypto flagship: quote, asset profile, technicals, market-wide Fear & Greed, derivatives
    positioning and on-chain health gathered concurrently. ``notes`` carries any partial failure.
    """

    symbol: str
    base: str
    quote: str
    quote_data: CryptoQuote | None = None
    profile: CryptoAssetProfile | None = None
    technicals: Technicals | None = None
    fear_greed: CryptoFearGreed | None = None
    derivatives: CryptoDerivatives | None = None
    onchain: CryptoOnChain | None = None
    notes: list[str] = []
