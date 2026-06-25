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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
