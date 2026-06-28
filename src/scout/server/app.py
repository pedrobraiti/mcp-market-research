"""MCP server — exposes Scout's research capabilities as tools for the agent.

Every tool is a stateless read: it takes its inputs (including an optional ``as_of`` date),
reads the world, and returns a JSON-serializable ``{"ok": ..., "data": ...}`` envelope.
Errors become ``{"ok": false, "error": ...}`` so the agent reads them instead of breaking.
Scout never places orders and never persists state — that is by design (see CLAUDE.md).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..analytics import compute_technicals
from ..domain.models import CryptoPriceHistory, Period, PriceBar, PriceHistory
from ..research import (
    build_calendar,
    build_classification,
    build_comparison,
    build_correlation,
    build_crypto_comparison,
    build_crypto_correlation,
    build_crypto_dossier,
    build_crypto_relative_strength,
    build_dossier,
    build_news_digest,
    build_relative_strength,
    build_sector_performance,
)
from .services import Services, build_services

_services: Services | None = None


def services() -> Services:
    global _services
    if _services is None:
        _services = build_services()
    return _services


mcp = FastMCP("mcp-market-research")


def _ok(data: Any) -> dict:
    return {"ok": True, "data": data}


def _err(exc: Exception) -> dict:
    return {"ok": False, "error": str(exc)}


def _parse_as_of(as_of: str | None) -> date | None:
    """Parse an optional ISO date (YYYY-MM-DD). Raises ValueError on a malformed value."""
    if as_of is None or not as_of.strip():
        return None
    return datetime.strptime(as_of.strip(), "%Y-%m-%d").date()


@mcp.tool()
async def company_dossier(symbol: str, depth: str = "full", as_of: str | None = None) -> dict:
    """Consolidated one-call research dossier for a US stock/ETF — the flagship tool.

    Fans several reads out in parallel and returns them together: a `snapshot`, plus (when
    `depth="full"`, the default) `fundamentals` and `dividends`. Use `depth="summary"` for a
    quick snapshot-only read. Pass `as_of` (YYYY-MM-DD) for a point-in-time view. If one source
    is momentarily unavailable the dossier still returns, with the gap recorded in `notes` —
    prefer this over calling the individual tools when you want the full picture at once.
    """
    svc = services()
    try:
        dossier = await build_dossier(
            svc.market_data, symbol, depth.strip().lower(), _parse_as_of(as_of)
        )
        return _ok(dossier.model_dump(mode="json"))
    except ValueError as exc:
        return _err(exc)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def search_symbols(query: str, limit: int = 10) -> dict:
    """Resolve a company name or partial ticker to matching symbols.

    The starting point when you have a name but not the ticker (e.g. "nvidia", "coca cola").
    Returns candidates with symbol, name, exchange and instrument type — pick the right ticker,
    then feed it to the other tools.
    """
    svc = services()
    try:
        result = await svc.market_data.search_symbols(query, int(limit))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def market_movers(category: str = "gainers", limit: int = 20) -> dict:
    """Market-wide top movers today — discovery WITHOUT a symbol in hand.

    `category` is "gainers", "losers" or "most_active". Returns the names moving most today
    (symbol, name, price, % change, volume) so you can ask "what's moving right now?" before you
    have a ticker. Raw market data, not a pick.
    """
    svc = services()
    try:
        result = await svc.market_data.get_movers(category, int(limit))
        return _ok(result.model_dump(mode="json"))
    except ValueError as exc:
        return _err(exc)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def compare(symbols: list[str], as_of: str | None = None) -> dict:
    """Compare several US stocks/ETFs side by side in one call.

    For each symbol, gathers price, market cap, trailing & forward P/E, dividend yield, revenue,
    net margin and sector (snapshot + fundamentals, in parallel). Pass `as_of` (YYYY-MM-DD) for a
    point-in-time view. A symbol whose data is unavailable still appears, with a `note`.
    """
    svc = services()
    try:
        result = await build_comparison(svc.market_data, symbols, _parse_as_of(as_of))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def classify(symbols: list[str], as_of: str | None = None) -> dict:
    """Sector, industry and market cap for several symbols in one call.

    The building block for "how much of my book is tech?": this returns the classification
    per symbol so the agent can aggregate exposure (the agent owns the position sizes; Scout
    just labels the names). A symbol whose data is missing gets a `note`.
    """
    svc = services()
    try:
        result = await build_classification(svc.market_data, symbols, _parse_as_of(as_of))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def news_digest(symbols: list[str], limit_per_symbol: int = 5) -> dict:
    """Recent headlines across several symbols in one call, newest first.

    For "any news that affects what I hold?" over a whole watchlist/portfolio — each item is
    tagged with its symbol and carries a link you can pass to `extract`. Headlines only.
    """
    svc = services()
    try:
        result = await build_news_digest(svc.market_data, symbols, int(limit_per_symbol))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def calendar(symbols: list[str], as_of: str | None = None) -> dict:
    """Upcoming earnings and ex-dividend dates across several symbols, sorted by date.

    Answers "what's coming up for my positions this week?" in one call. Pass `as_of`
    (YYYY-MM-DD) to treat that date as "now". Returns events (symbol, type, date) only.
    """
    svc = services()
    try:
        result = await build_calendar(svc.market_data, symbols, _parse_as_of(as_of))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def correlation_matrix(
    symbols: list[str], period: str = "6mo", as_of: str | None = None
) -> dict:
    """Pairwise return correlation between symbols — to see real diversification.

    Fetches each symbol's daily prices over `period`, aligns them on common trading days and
    returns the Pearson correlation of daily returns for every pair (1.0 = move together,
    -1.0 = move opposite, ~0 = unrelated). Needs at least two symbols with overlapping history.
    """
    svc = services()
    try:
        result = await build_correlation(
            svc.market_data, symbols, period.strip(), _parse_as_of(as_of)
        )
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def company_snapshot(symbol: str, as_of: str | None = None) -> dict:
    """Light single-call portrait of a US stock/ETF: price, day move and key multiples.

    Returns name, currency, price, previous_close, change/percent, market cap, trailing &
    forward P/E, dividend yield, 52-week high/low, sector and industry. Also `recent_splits`
    (newest first) — so a split-adjusted price (e.g. NFLX post-10:1) isn't read as "wrong"
    against pre-split memory; price and the 52-week range are already split-adjusted. Pass
    `as_of` (YYYY-MM-DD) to read a past date — historical reads return price/move (plus splits
    up to that date) only (point-in-time multiples are not available yet). `data` is null if the
    symbol can't be resolved.
    """
    svc = services()
    try:
        snapshot = await svc.market_data.get_snapshot(symbol, _parse_as_of(as_of))
        return _ok(snapshot.model_dump(mode="json") if snapshot else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def quality_metrics(symbol: str, as_of: str | None = None) -> dict:
    """Derived quality & return ratios for a US company.

    Returns ROE, ROA, gross/operating/net margins, year-over-year revenue & earnings growth, and
    multi-year revenue & net-income CAGR (computed from the income statements). Raw numbers — it
    does not score "quality" or "moat"; you read ROE/margins/CAGR and judge.

    NOTE on basis: ROE, ROA and the margins here are the provider's trailing-twelve-month (TTM)
    figures — they will NOT reconcile with a single fiscal-year statement (e.g. ROE here ≠ that
    year's net income / equity from `sec_financials`), since the numerator is TTM, not the
    fiscal year. Only the CAGR fields are derived from the annual statements. Use `fundamentals`
    / `sec_financials` for fiscal-year ratios.
    """
    svc = services()
    try:
        result = await svc.market_data.get_quality_metrics(symbol, _parse_as_of(as_of))
        return _ok(result.model_dump(mode="json") if result else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def relative_strength(
    symbols: list[str], benchmark: str = "SPY", period: str = "3mo", as_of: str | None = None
) -> dict:
    """Each symbol's total return over `period` vs a `benchmark` (default SPY).

    Returns the period return per symbol and its excess over the benchmark, sorted strongest
    first — the leadership/laggard read for momentum. Raw returns, not a "buy the strong" call.
    """
    svc = services()
    try:
        result = await build_relative_strength(
            svc.market_data, symbols, benchmark.strip(), period.strip(), _parse_as_of(as_of)
        )
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def fundamentals(symbol: str, period: str = "annual", as_of: str | None = None) -> dict:
    """Core fundamentals for a US company: income, balance-sheet and cash-flow figures.

    `period` is "annual" or "quarterly". Returns revenue, gross/operating income, net income,
    margins, total debt/cash/assets, stockholders' equity and free cash flow, for the latest
    fiscal period at or before `as_of`, plus a derived block. Valuation/quality: net_debt,
    net_debt_to_fcf, fcf_margin, gross_profitability (Novy-Marx), pretax ROIC. Liquidity/leverage:
    current_ratio, working_capital, debt_to_equity, EBITDA, net_debt_to_ebitda, interest_coverage,
    and the Altman Z″ distress score (book-equity variant; >2.6 safe, <1.1 distress). On a live read
    (paired with current market cap): FCF & earnings yield, enterprise value, EV/EBIT, EV/EBITDA,
    EV/Sales, EBIT/EV. Each derived field is null when an input is missing or its denominator isn't
    positive (so a value never silently misleads). Raw numbers, not a rating. `data` is null if no
    statements are available. (`as_of` is YYYY-MM-DD.)
    """
    svc = services()
    try:
        parsed_period = Period(period.strip().lower())
        result = await svc.market_data.get_fundamentals(symbol, parsed_period, _parse_as_of(as_of))
        return _ok(result.model_dump(mode="json") if result else None)
    except ValueError:
        return _err(ValueError("period must be 'annual' or 'quarterly'."))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def dividends(symbol: str, as_of: str | None = None) -> dict:
    """Dividend history and income quality for a US stock/ETF.

    Returns the payment history (ex-date + amount), trailing-12-month total, trailing yield,
    the consecutive-growth streak (complete calendar years of non-decreasing dividend) and a
    `had_cut` flag. Pass `as_of` (YYYY-MM-DD) to evaluate the history up to a past date. This
    is raw data — it does NOT judge whether the dividend is "safe"; the agent concludes from
    the streak/cut/yield. `data` is null if the symbol can't be resolved (an empty history with
    no payments means a valid symbol that simply pays no dividend).
    """
    svc = services()
    try:
        result = await svc.market_data.get_dividends(symbol, _parse_as_of(as_of))
        return _ok(result.model_dump(mode="json") if result else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def price_history(
    symbol: str, period: str = "6mo", interval: str = "1d", as_of: str | None = None
) -> dict:
    """OHLCV price history for a US stock/ETF.

    `period` is a yfinance range (e.g. "1mo", "3mo", "6mo", "1y", "2y", "5y", "max");
    `interval` is the bar size (e.g. "1d", "1wk", "1h", "5m"). Pass `as_of` (YYYY-MM-DD) to
    truncate at a past date. Returns a list of bars (date + open/high/low/close/volume).
    """
    svc = services()
    try:
        result = await svc.market_data.get_price_history(
            symbol, period.strip(), interval.strip(), _parse_as_of(as_of)
        )
        return _ok(result.model_dump(mode="json") if result else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def technicals(symbol: str, as_of: str | None = None) -> dict:
    """Technical indicators for a US stock/ETF, computed from ~2y of daily bars.

    Returns last price, SMA(50/200), EMA(20), RSI(14), MACD (line/signal/histogram), ATR(14)
    and the 52-week high/low, plus a derived risk/momentum layer: annualized volatility
    (close-to-close and Yang-Zhang OHLC), ATR%, 52w range position, the Mayer Multiple
    (price/SMA200), Sharpe/Sortino/Calmar, max drawdown (+ underwater bars), return skew/kurtosis
    and momentum (3m/6m/12m and 12-1).
    Ratios are annualized at 252 trading days with risk-free=0. These are **raw numbers, not a
    verdict** — it reports RSI, drawdown, Sharpe; it does not say "overbought" or "good risk".
    Pass `as_of` (YYYY-MM-DD) for a point-in-time read. `data` is null if there isn't enough
    price history (each derived field is null until its own minimum sample is met).
    """
    svc = services()
    try:
        history = await svc.market_data.get_price_history(symbol, "2y", "1d", _parse_as_of(as_of))
        if history is None or not history.bars:
            return _ok(None)
        return _ok(compute_technicals(history).model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def filings(
    symbol: str, form_type: str | None = None, limit: int = 20, as_of: str | None = None
) -> dict:
    """Recent SEC EDGAR filings for a US company — authoritative, straight from the source.

    Returns each filing's form (e.g. "10-K", "10-Q", "8-K"), filing & report dates, accession
    number and a link to the primary document. Pass `form_type` to filter (e.g. "10-K") and
    `as_of` (YYYY-MM-DD) to see only filings up to a past date. Use this to read primary sources
    and to cross-check figures from other tools. `data` is null if the symbol can't be resolved.

    Requires the SCOUT_SEC_USER_AGENT env var (SEC policy: an identifiable User-Agent).
    """
    svc = services()
    if svc.filings is None or not svc.settings.sec_user_agent.strip():
        return _err(
            ValueError(
                "Set SCOUT_SEC_USER_AGENT (e.g. 'Your Name you@email.com') — SEC EDGAR "
                "requires an identifiable User-Agent."
            )
        )
    try:
        result = await svc.filings.get_filings(symbol, form_type, int(limit), _parse_as_of(as_of))
        return _ok(result.model_dump(mode="json") if result else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def news(symbol: str, limit: int = 10) -> dict:
    """Recent news headlines for a US stock/ETF: title, publisher, date and a link.

    Returns the latest items so you can scan what's moving a name — and pass an interesting
    `url` to `extract` to read the full story. Headlines only; it does not score sentiment.

    NOT EXHAUSTIVE for corporate events: a quiet news feed does not mean nothing happened. For
    capital-structure changes (equity raises, dilution, buybacks, M&A) cross-check the primary
    source — `filings(symbol, form_type="8-K")` — before acting on a name.
    """
    svc = services()
    try:
        result = await svc.market_data.get_news(symbol, int(limit))
        return _ok(result.model_dump(mode="json") if result else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def options_volatility(symbol: str, expiry: str | None = None) -> dict:
    """Implied volatility and the options-implied expected move for a US stock/ETF.

    Returns ATM implied vol and the 1-sigma expected move (% and $ range) to the chosen `expiry`
    (YYYY-MM-DD; nearest by default), plus derived reads from the same chain: iv_skew (OTM put vs
    call IV, >0 = puts richer/fear), put/call ratios (volume & OI), and the volatility risk premium
    — ATM IV minus trailing realized vol, with the iv_rv_ratio (>1 = options look rich). The VRP is
    the stateless stand-in for IV rank (true IV-rank/percentile need stored IV history, which a
    stateless server can't provide, so they're intentionally omitted). `data` is null if no options
    trade. Raw numbers, not a trade call.
    """
    svc = services()
    try:
        result = await svc.market_data.get_options_volatility(symbol, expiry)
        return _ok(result.model_dump(mode="json") if result else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def earnings(symbol: str, as_of: str | None = None) -> dict:
    """Earnings calendar and history for a US company.

    Returns the next earnings date and past events with EPS estimate, reported EPS and the
    surprise %, plus derived consistency measures over past prints: beat_rate (share that beat),
    surprise_streak (consecutive most-recent beats), avg_surprise and surprise_consistency (stdev
    of the surprise — lower is steadier/more predictable). Pass `as_of` (YYYY-MM-DD) to treat that
    date as "now" when splitting upcoming vs past. Useful to know if a binary event is near, and
    how reliably the company has cleared the bar, before acting on a name.
    """
    svc = services()
    try:
        result = await svc.market_data.get_earnings(symbol, _parse_as_of(as_of))
        return _ok(result.model_dump(mode="json") if result else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def retail_buzz(symbol: str | None = None, limit: int = 20) -> dict:
    """Reddit (WSB/stocks) mention buzz — a retail-attention signal.

    Without `symbol`, returns the top trending tickers by Reddit mentions (rank, mentions, and the
    change vs 24h ago). With `symbol`, returns that name's buzz (or a note if it isn't trending).
    This is **attention/buzz, not sentiment** and skews toward meme names — raw counts to interpret.
    """
    svc = services()
    if svc.retail_buzz is None:
        return _err(ValueError("Retail buzz is not configured."))
    try:
        result = await svc.retail_buzz.get_buzz(symbol, int(limit))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def wikipedia_attention(article: str, days: int = 30) -> dict:
    """Daily Wikipedia pageviews for an article — an attention proxy (keyless, official).

    Pass the exact Wikipedia article title (e.g. "Tesla, Inc.", "NVIDIA"). Returns daily views
    over the last `days` plus the total — rising views mean a name is in the public eye. Like
    Google Trends but stable and keyless. Raw counts, not a signal verdict.
    """
    svc = services()
    if svc.attention is None:
        return _err(ValueError("Attention source is not configured."))
    try:
        result = await svc.attention.get_pageviews(article, int(days))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def ownership(symbol: str) -> dict:
    """Who owns the stock: insider & institution %, top institutions, recent insider trades.

    Public-record data (13F / Form 4): insider-held and institution-held %, the largest
    institutional holders, and recent insider buy/sell transactions. A skin-in-the-game signal —
    raw facts, not a verdict; you interpret what insider buying/selling implies.
    """
    svc = services()
    try:
        result = await svc.market_data.get_ownership(symbol)
        return _ok(result.model_dump(mode="json") if result else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def analyst_view(symbol: str) -> dict:
    """Sell-side analyst consensus and price targets for a US stock.

    Returns the consensus recommendation (key + mean, 1=strong buy … 5=sell), the number of
    analysts, and mean/median/high/low price targets vs the current price, plus derived
    upside_pct (mean target vs current price) and target_dispersion (high-low spread over the
    mean — low = tight consensus/high conviction, wide = disagreement). This is **what
    third-party analysts say, reported as data** — not Scout's recommendation; you weigh it.
    """
    svc = services()
    try:
        result = await svc.market_data.get_analyst_view(symbol)
        return _ok(result.model_dump(mode="json") if result else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def sector_performance(period: str = "3mo", as_of: str | None = None) -> dict:
    """Total return of each US sector over `period`, via the 11 SPDR sector ETFs.

    Shows where money has rotated (sectors sorted best to worst) — e.g. "what's leading the last
    3 months?". Pass `as_of` (YYYY-MM-DD) for a past window. Raw returns, not a rotation call.
    """
    svc = services()
    try:
        result = await build_sector_performance(
            svc.market_data, period.strip(), _parse_as_of(as_of)
        )
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def etf_holdings(symbol: str) -> dict:
    """An ETF's declared basket: top holdings (with weights) and sector weights.

    The structured way to open a theme — e.g. the names inside a defense (ITA) or uranium (URA)
    ETF — straight from the issuer's declared holdings, not opinion. `data` is null if the
    symbol isn't a fund (or holdings aren't published).
    """
    svc = services()
    try:
        result = await svc.market_data.get_etf_holdings(symbol)
        return _ok(result.model_dump(mode="json") if result else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def world_macro(country: str = "USA", codes: list[str] | None = None) -> dict:
    """Country-level macro indicators from the **World Bank** (global, official, keyless).

    Returns the latest GDP growth, inflation, unemployment, GDP per capita and population for a
    `country` (ISO code, default "USA"). Lower-frequency structural context — for US trading-day
    macro use `macro_context` (FRED); this broadens the picture to any country.
    """
    svc = services()
    if svc.world_macro is None:
        return _err(ValueError("World macro source is not configured."))
    try:
        result = await svc.world_macro.get_indicators(country, codes)
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def treasury_data() -> dict:
    """Official US Treasury fiscal data (keyless): total public debt and average interest rates.

    Returns the latest total public debt outstanding and the average interest rate the Treasury
    pays by security type — authoritative figures straight from the US Treasury Fiscal Data API.
    """
    svc = services()
    if svc.treasury is None:
        return _err(ValueError("Treasury source is not configured."))
    try:
        result = await svc.treasury.get_data()
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def macro_context(as_of: str | None = None) -> dict:
    """Key US macro indicators (from FRED): policy rate, the yield curve, jobs, inflation, vol.

    Returns the latest value and date of each series — Fed Funds rate, 10Y / 3M / 2Y Treasury
    yields, the 10Y-2Y spread, unemployment, CPI (index), the VIX, 10y breakeven inflation, the
    10y TIPS real yield and the US high-yield credit spread — plus a `derived` block that turns
    those raw series into regime numbers: CPI inflation YoY (and 3m annualized), real Fed-funds &
    real 10y (ex-post) and the ex-ante real 10y (TIPS), market-expected inflation (breakeven), the
    Sahm recession gap (+ signal), the VIX z-score & percentile, yield-curve inversion (+ how
    long), a 12-month recession probability (NY-Fed term-spread probit), and the high-yield credit
    spread with its z-score (a financial-stress gauge that often widens before equities fall). A
    bare CPI index level says nothing alone — the derived block is what's usable. Pass `as_of`
    (YYYY-MM-DD) for a point-in-time read. Numbers and explicit measures, not a regime verdict.
    """
    svc = services()
    if svc.macro is None:
        return _err(ValueError("Macro source is not configured."))
    try:
        snapshot = await svc.macro.get_macro_context(_parse_as_of(as_of))
        return _ok(snapshot.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def news_search(query: str, limit: int = 20, days: int = 7) -> dict:
    """Free-text news/event search across global media (GDELT) — by THEME or company name.

    Unlike `news` (which needs a ticker), this searches worldwide coverage for any query — a
    thesis ("AI data center power"), an event, or a company name — over the last `days`. Returns
    articles (title, source, date, link) to read via `extract`. Capture only, no sentiment score.

    NOT EXHAUSTIVE: this free feed can miss capital-structure events (equity raises, dilution,
    buybacks, M&A). Do NOT rely on it alone to clear a name of such events — consult primary
    filings via `filings(symbol, form_type="8-K")` / `filing_search` before an execution-grade
    thesis. If `source_status` is set (e.g. "unavailable: rate_limited"), the source was
    unreachable (429/timeout) — that is "couldn't fetch", NOT "no news"; retry or abstain.
    """
    svc = services()
    if svc.news_search is None:
        return _err(ValueError("News search is not configured."))
    try:
        result = await svc.news_search.search_news(query, int(limit), int(days))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def extract(url: str) -> dict:
    """Fetch a web page and return its main content as clean, token-efficient markdown.

    A research aid: YOU pick the URL (e.g. a source found while researching), this strips the
    nav/ads/boilerplate and returns just the article/body so you read more signal per token. It
    does not summarize or judge — that's your job. On a paywall or anti-bot block it honestly
    returns `fetched_ok=false` with a note (it can't bypass those). Good for primary sources
    (press releases, IR pages, news) the agent wants to read in full.
    """
    svc = services()
    if svc.extractor is None:
        return _err(ValueError("Extractor is not configured."))
    try:
        page = await svc.extractor.extract(url)
        return _ok(page.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def filing_search(query: str, forms: str | None = None, limit: int = 10) -> dict:
    """Full-text search across ALL SEC EDGAR filings — discover companies by what they disclose.

    The top-down "thesis → names" tool: search a phrase ("small modular reactor", "GLP-1") and get
    the companies/filings that mention it, with name, ticker, form, date and a link. Optional
    `forms` filter (e.g. "10-K"). Official data, not opinion. Requires SCOUT_SEC_USER_AGENT.
    """
    svc = services()
    if svc.filings is None or not svc.settings.sec_user_agent.strip():
        return _err(
            ValueError(
                "Set SCOUT_SEC_USER_AGENT (e.g. 'Your Name you@email.com') — SEC EDGAR "
                "requires an identifiable User-Agent."
            )
        )
    try:
        result = await svc.filings.search_filings(query, forms, int(limit))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def sec_financials(symbol: str, as_of: str | None = None) -> dict:
    """Authoritative annual financials for a US company from **SEC EDGAR XBRL**.

    Returns the reported revenue, gross/operating income, net income, total assets and
    stockholders' equity for the latest fiscal year (10-K) at or before `as_of` (YYYY-MM-DD) —
    each line tagged with the exact us-gaap concept, period end, form and filing date. Use it to
    **cross-check** `fundamentals` (which comes from yfinance) against the primary source. `data`
    is null if the symbol can't be resolved. Requires SCOUT_SEC_USER_AGENT (SEC policy).
    """
    svc = services()
    if svc.financials is None or not svc.settings.sec_user_agent.strip():
        return _err(
            ValueError(
                "Set SCOUT_SEC_USER_AGENT (e.g. 'Your Name you@email.com') — SEC EDGAR "
                "requires an identifiable User-Agent."
            )
        )
    try:
        result = await svc.financials.get_financials(symbol, _parse_as_of(as_of))
        return _ok(result.model_dump(mode="json") if result else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


def _crypto_to_price_history(history: CryptoPriceHistory) -> PriceHistory:
    """Adapt crypto OHLCV onto the equities ``PriceHistory`` so ``compute_technicals`` is reused."""
    bars = [
        PriceBar(
            date=bar.timestamp.date(),
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
        )
        for bar in history.bars
    ]
    return PriceHistory(
        symbol=history.symbol, interval=history.timeframe, bars=bars, as_of=history.as_of
    )


@mcp.tool()
async def crypto_quote(symbol: str) -> dict:
    """Live spot quote for a crypto pair: last/bid/ask and the 24h move.

    `symbol` is a CCXT pair like "BTC/USDT" (or just "BTC" — the default quote, USDT, is added).
    Returns last/bid/ask, 24h high/low, 24h % change and base/quote volume from the configured
    exchange (default Binance). The crypto analog of `company_snapshot`. `data` is null if the
    pair can't be resolved. Raw market data, not a trade call.
    """
    svc = services()
    if svc.crypto_market_data is None:
        return _err(ValueError("Crypto market data is not configured."))
    try:
        result = await svc.crypto_market_data.get_quote(symbol)
        return _ok(result.model_dump(mode="json") if result else None)
    except ValueError as exc:
        return _err(exc)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_price_history(
    symbol: str, timeframe: str = "1d", limit: int = 200, as_of: str | None = None
) -> dict:
    """OHLCV candle history for a crypto pair.

    `symbol` is a CCXT pair ("BTC/USDT" or "BTC"); `timeframe` is a CCXT bar size
    ("1m","5m","15m","1h","4h","1d","1w"); `limit` is how many recent candles (max 1000). Pass
    `as_of` (YYYY-MM-DD) to drop candles after that date. Each bar carries a UTC `timestamp` and
    open/high/low/close/volume. The crypto analog of `price_history`.
    """
    svc = services()
    if svc.crypto_market_data is None:
        return _err(ValueError("Crypto market data is not configured."))
    try:
        result = await svc.crypto_market_data.get_price_history(
            symbol, timeframe.strip(), int(limit), _parse_as_of(as_of)
        )
        return _ok(result.model_dump(mode="json") if result else None)
    except ValueError as exc:
        return _err(exc)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_technicals(symbol: str, as_of: str | None = None) -> dict:
    """Technical indicators for a crypto pair, computed from ~300 daily candles.

    Same indicator set as the equities `technicals` tool plus the derived risk/momentum layer
    (volatility, ATR%, 52w range position, Mayer Multiple price/SMA200, Sharpe/Sortino/Calmar,
    max drawdown, skew/kurtosis, momentum), reusing the same pure math. Crypto-calibrated: ratios
    annualize at 365 (24/7) and
    OHLC volatility uses the Rogers-Satchell estimator (no overnight gap to model). `symbol` is a
    CCXT pair ("BTC/USDT" or "BTC"); pass `as_of` (YYYY-MM-DD) for a point-in-time read. **Raw
    numbers, not a verdict** (no "overbought"/"uptrend"). `data` is null if there isn't enough
    history.
    """
    svc = services()
    if svc.crypto_market_data is None:
        return _err(ValueError("Crypto market data is not configured."))
    try:
        history = await svc.crypto_market_data.get_price_history(
            symbol, "1d", 300, _parse_as_of(as_of)
        )
        if history is None or not history.bars:
            return _ok(None)
        tech = compute_technicals(
            _crypto_to_price_history(history), periods_per_year=365, overnight_gaps=False
        )
        return _ok(tech.model_dump(mode="json"))
    except ValueError as exc:
        return _err(exc)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_asset_profile(symbol: str) -> dict:
    """Supply, market cap, rank and ATH for a crypto asset — the 'fundamentals' of crypto.

    `symbol` is the base asset ("BTC", or a pair like "BTC/USDT" — only the base is used).
    Returns circulating/total/max supply, USD market cap & rank, 24h volume, all-time-high
    price/date with % from ATH, and derived tokenomics: float_ratio (circulating/total),
    issuance_progress (circulating/max — % of final supply minted) and future_dilution
    ((max−circulating)/circulating — supply overhang); the last two are null for uncapped assets
    (no max supply, e.g. ETH). From Coinpaprika, keyed by the asset, not one exchange. Raw facts,
    not a valuation. `data` is null if the asset can't be resolved.
    """
    svc = services()
    if svc.crypto_assets is None:
        return _err(ValueError("Crypto asset source is not configured."))
    base = symbol.strip().replace("-", "/").replace("_", "/").split("/")[0]
    try:
        result = await svc.crypto_assets.get_profile(base)
        return _ok(result.model_dump(mode="json") if result else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_fear_greed(days: int = 30) -> dict:
    """The Crypto Fear & Greed Index (0-100) — market-wide sentiment, with daily history.

    Returns the current value and classification (Extreme Fear … Extreme Greed) plus the daily
    history over the last `days` (alternative.me, keyless). Market-level, NOT per-coin — a mood
    gauge the agent reads alongside price. Raw index, not a buy/sell signal.
    """
    svc = services()
    if svc.crypto_sentiment is None:
        return _err(ValueError("Crypto sentiment source is not configured."))
    try:
        result = await svc.crypto_sentiment.get_fear_greed(int(days))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_buzz(symbol: str | None = None, limit: int = 20) -> dict:
    """Reddit crypto mention buzz — a retail-attention signal for coins.

    Without `symbol`, returns the top trending coins by Reddit mentions (rank, mentions, change
    vs 24h ago). With `symbol` (e.g. "BTC"), returns that coin's buzz (or a note if it isn't
    trending). The crypto analog of `retail_buzz` (ApeWisdom's `all-crypto` filter). This is
    **attention/buzz, not sentiment**, and skews toward meme coins — raw counts to interpret.
    """
    svc = services()
    if svc.crypto_buzz is None:
        return _err(ValueError("Crypto buzz is not configured."))
    try:
        result = await svc.crypto_buzz.get_buzz(symbol, int(limit))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_search(query: str, limit: int = 10) -> dict:
    """Resolve a crypto name or partial symbol to assets (the entry point when you lack the ticker).

    Crypto naming is messy (many forks/clones share a symbol); this returns candidates with base,
    name, provider id and rank (best/most-prominent first) so you pick the right one, then feed the
    base to the other crypto tools. Coinpaprika, keyless.
    """
    svc = services()
    if svc.crypto_assets is None:
        return _err(ValueError("Crypto asset source is not configured."))
    try:
        result = await svc.crypto_assets.search(query, int(limit))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_movers(category: str = "gainers", limit: int = 20) -> dict:
    """Market-wide top crypto movers on the configured exchange — discovery WITHOUT a symbol.

    `category` is "gainers", "losers" or "most_active" (by 24h quote volume). Returns the pairs
    moving most today (symbol, last, % change, volume) so you can ask "what's moving in crypto?"
    before you have a ticker. Uses the exchange's own tickers (no 429 issues). Raw, not a pick.
    """
    svc = services()
    if svc.crypto_market_data is None:
        return _err(ValueError("Crypto market data is not configured."))
    try:
        result = await svc.crypto_market_data.get_movers(category, int(limit))
        return _ok(result.model_dump(mode="json"))
    except ValueError as exc:
        return _err(exc)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_order_book(symbol: str, limit: int = 20) -> dict:
    """Order-book top-of-book and aggregated depth for a pair — a pre-trade liquidity/slippage read.

    Returns best bid/ask, the spread (absolute & %), aggregated base-asset depth per side, the top
    levels, and two derived microstructure measures: `imbalance` ((bid−ask depth)/(bid+ask), −1..1
    — short-horizon directional pressure) and `microprice` (size-weighted fair price that leans to
    the thinner side, a better next-trade estimate than the mid). Use it to judge whether a pair is
    liquid enough to size into without bad slippage. `data` is null if no book is returned. Raw
    microstructure, not a call.
    """
    svc = services()
    if svc.crypto_market_data is None:
        return _err(ValueError("Crypto market data is not configured."))
    try:
        result = await svc.crypto_market_data.get_order_book(symbol, int(limit))
        return _ok(result.model_dump(mode="json") if result else None)
    except ValueError as exc:
        return _err(exc)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_compare(symbols: list[str]) -> dict:
    """Compare several crypto assets side by side in one call.

    For each symbol, gathers price + 24h change (quote) and market cap, rank & circulating supply
    (profile), in parallel. A symbol whose data is unavailable still appears, with a `note`. Raw
    figures to weigh, not a ranking.
    """
    svc = services()
    if svc.crypto_market_data is None or svc.crypto_assets is None:
        return _err(ValueError("Crypto sources are not configured."))
    try:
        result = await build_crypto_comparison(svc.crypto_market_data, svc.crypto_assets, symbols)
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_correlation_matrix(
    symbols: list[str], timeframe: str = "1d", limit: int = 120
) -> dict:
    """Pairwise return correlation between crypto pairs — to see real diversification.

    Fetches each pair's candles over `limit` bars at `timeframe`, aligns them on common days and
    returns the Pearson correlation of returns for every pair (1.0 = move together, ~0 = unrelated).
    Crypto is highly co-correlated (most alts track BTC) — this quantifies it. Needs ≥2 pairs.
    """
    svc = services()
    if svc.crypto_market_data is None:
        return _err(ValueError("Crypto market data is not configured."))
    try:
        result = await build_crypto_correlation(
            svc.crypto_market_data, symbols, timeframe.strip(), int(limit)
        )
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_relative_strength(
    symbols: list[str], benchmark: str = "BTC", timeframe: str = "1d", limit: int = 90
) -> dict:
    """Each pair's return over a window vs a benchmark (default BTC) — the leadership read.

    Returns each symbol's % return and its excess over the benchmark, strongest first. "Is this alt
    outperforming BTC?" is the core crypto rotation question. Raw returns, not a buy call.
    """
    svc = services()
    if svc.crypto_market_data is None:
        return _err(ValueError("Crypto market data is not configured."))
    try:
        result = await build_crypto_relative_strength(
            svc.crypto_market_data, symbols, benchmark.strip(), timeframe.strip(), int(limit)
        )
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_onchain(asset: str = "BTC") -> dict:
    """On-chain network-health metrics for a chain (raw facts, not a verdict).

    `asset` is "BTC" (mempool.space: recommended fees, hashrate, difficulty change) or "ETH"
    (Blockscout: total addresses/transactions, gas prices, network utilization). The crypto analog
    of fundamentals — chain activity & cost. Other assets return a note (no keyless source wired).
    """
    svc = services()
    if svc.crypto_onchain is None:
        return _err(ValueError("Crypto on-chain source is not configured."))
    try:
        result = await svc.crypto_onchain.get_onchain(asset)
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_derivatives(symbol: str) -> dict:
    """Perp funding rate & open interest across exchanges — positioning CONTEXT (never executed).

    For a base asset (e.g. "BTC"), returns per-venue (Binance, Bybit, OKX) the perpetual funding
    rate, its annualized form, next funding time, mark price and open interest (incl. USD value),
    plus cross-venue aggregates: OI-weighted funding consensus (annualized too), funding dispersion
    across venues (a stress/arbitrage signal) and total OI in USD. High positive funding = crowded
    longs; rising OI = leverage building. Annualized figures assume an 8h funding interval (the
    venues' default). Execution is spot-only, so this is sentiment only — not a trade.
    """
    svc = services()
    if svc.crypto_derivatives is None:
        return _err(ValueError("Crypto derivatives source is not configured."))
    try:
        result = await svc.crypto_derivatives.get_derivatives(symbol)
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_implied_vol(asset: str = "BTC") -> dict:
    """The Deribit DVOL index ('crypto VIX') — options-implied volatility for BTC or ETH.

    Returns the current DVOL value, its z-score and percentile vs the trailing ~6-month window (the
    vol regime — cheap vs expensive relative to its own history), plus the daily history. It's how
    much swing the options market is pricing — useful to size a stop or read whether vol is
    cheap/expensive. BTC/ETH only (others return a note). Raw index, not a trade call.
    """
    svc = services()
    if svc.crypto_vol is None:
        return _err(ValueError("Crypto volatility source is not configured."))
    try:
        result = await svc.crypto_vol.get_implied_vol(asset)
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def defi_overview(slug: str | None = None) -> dict:
    """DeFi total value locked (TVL) — by chain, or one protocol's breakdown.

    Without `slug`, returns total DeFi TVL and the top chains by TVL. With `slug` (e.g. "aave",
    "uniswap"), returns that protocol's TVL split by chain. Ecosystem traction/health (DefiLlama,
    keyless). Raw TVL, not a verdict.
    """
    svc = services()
    if svc.defi is None:
        return _err(ValueError("DeFi source is not configured."))
    try:
        result = await svc.defi.get_tvl(slug)
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def stablecoin_supply() -> dict:
    """Stablecoin circulation and peg status (DefiLlama) — liquidity & systemic-risk read.

    Returns total stablecoin circulation and the largest stablecoins with peg type/mechanism, price
    and peg deviation. A depeg or a sharp circulation change is a market-wide risk signal the agent
    should weigh (e.g. before sizing into a USDT-quoted pair). Raw facts, not a verdict.
    """
    svc = services()
    if svc.defi is None:
        return _err(ValueError("DeFi source is not configured."))
    try:
        result = await svc.defi.get_stablecoins()
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def defi_yields(
    chain: str | None = None, project: str | None = None, min_tvl: float = 1_000_000
) -> dict:
    """DeFi yield/APY pools (DefiLlama), filterable — where on-chain yield is, as context.

    Returns pools (project, chain, symbol, TVL, APY incl. base vs reward), highest APY first,
    filtered by `chain`, `project` and `min_tvl` (USD floor, default $1M to skip dust). Context for
    where capital earns on-chain — not a recommendation to farm.
    """
    svc = services()
    if svc.defi is None:
        return _err(ValueError("DeFi source is not configured."))
    try:
        result = await svc.defi.get_yields(chain, project, float(min_tvl))
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_macro() -> dict:
    """Crypto-wide macro snapshot: total market cap, BTC/ETH dominance, DeFi share (CoinGecko).

    Returns total crypto market cap & 24h volume, the 24h market-cap change, BTC and ETH dominance,
    and DeFi market cap/dominance — the regime backdrop (alt season vs BTC-dominant). Note:
    CoinGecko's keyless tier rate-limits; a 429 returns an honest error. Raw levels, not a call.
    """
    svc = services()
    if svc.crypto_macro is None:
        return _err(ValueError("Crypto macro source is not configured."))
    try:
        result = await svc.crypto_macro.get_macro()
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_sectors() -> dict:
    """Per-category (sector) performance for crypto (CoinGecko) — where money rotated.

    Returns crypto categories (L1, DeFi, AI, memecoin, RWA…) with market cap, 24h change, volume and
    top coins — the crypto analog of `sector_performance`. Note: CoinGecko keyless rate-limits (429
    returns an honest error). Raw returns, not a rotation call.
    """
    svc = services()
    if svc.crypto_macro is None:
        return _err(ValueError("Crypto macro source is not configured."))
    try:
        result = await svc.crypto_macro.get_sectors()
        return _ok(result.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def crypto_dossier(symbol: str, depth: str = "full") -> dict:
    """Consolidated one-call crypto portrait — the flagship, fanning several reads out in parallel.

    Returns a `quote_data` + `profile`, plus (when `depth="full"`, the default) `technicals`,
    market-wide `fear_greed`, `derivatives` positioning and `onchain` health — all concurrently.
    Use `depth="summary"` for quote + profile only. Partial failures are recorded in `notes`. Prefer
    this over calling the crypto tools one by one when you want the full picture of a pair at once.
    """
    svc = services()
    if (
        svc.crypto_market_data is None
        or svc.crypto_assets is None
        or svc.crypto_sentiment is None
        or svc.crypto_derivatives is None
        or svc.crypto_onchain is None
    ):
        return _err(ValueError("Crypto sources are not configured."))
    try:
        dossier = await build_crypto_dossier(
            svc.crypto_market_data,
            svc.crypto_assets,
            svc.crypto_sentiment,
            svc.crypto_derivatives,
            svc.crypto_onchain,
            symbol,
            depth.strip().lower(),
        )
        return _ok(dossier.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
