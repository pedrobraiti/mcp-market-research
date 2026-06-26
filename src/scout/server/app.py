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
from ..domain.models import Period
from ..research import build_dossier
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
async def company_snapshot(symbol: str, as_of: str | None = None) -> dict:
    """Light single-call portrait of a US stock/ETF: price, day move and key multiples.

    Returns name, currency, price, previous_close, change/percent, market cap, trailing &
    forward P/E, dividend yield, 52-week high/low, sector and industry. Pass `as_of`
    (YYYY-MM-DD) to read a past date — historical reads return price/move only (point-in-time
    multiples are not available yet). `data` is null if the symbol can't be resolved.
    """
    svc = services()
    try:
        snapshot = await svc.market_data.get_snapshot(symbol, _parse_as_of(as_of))
        return _ok(snapshot.model_dump(mode="json") if snapshot else None)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
async def fundamentals(symbol: str, period: str = "annual", as_of: str | None = None) -> dict:
    """Core fundamentals for a US company: income, balance-sheet and cash-flow figures.

    `period` is "annual" or "quarterly". Returns revenue, gross/operating income, net income,
    derived gross/operating/net margins, total debt, total cash and free cash flow, for the
    latest fiscal period at or before `as_of` (YYYY-MM-DD; omit for the latest). `data` is null
    if no statements are available for the symbol.
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
    and the 52-week high/low. These are **raw numbers, not a verdict** — e.g. it reports RSI and
    price-vs-SMA, it does not say "overbought" or "uptrend"; you draw the conclusion. Pass `as_of`
    (YYYY-MM-DD) for a point-in-time read. `data` is null if there isn't enough price history.
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
async def macro_context(as_of: str | None = None) -> dict:
    """Key US macro indicators (from FRED): policy rate, the yield curve, jobs, inflation, vol.

    Returns the latest value and date of each series — Fed Funds rate, 10Y & 2Y Treasury yields,
    the 10Y-2Y spread, unemployment, CPI (index) and the VIX. Pass `as_of` (YYYY-MM-DD) for a
    point-in-time read. Raw levels, not a regime call — you interpret risk-on/off from the numbers.
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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
