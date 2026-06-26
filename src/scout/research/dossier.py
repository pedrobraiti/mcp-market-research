"""``company_dossier`` — fan several reads out in parallel and consolidate.

This is the embodiment of the "fat, purposeful tool with internal parallelism" principle:
one call, several sources gathered concurrently with ``asyncio.gather``, returned as one
structured object. A failure in one read becomes a note, not a total failure.
"""

from __future__ import annotations

import asyncio
from datetime import date

from ..analytics import compute_technicals
from ..domain.models import CompanyDossier, Period
from ..domain.ports import MarketDataSource

DEPTHS = ("summary", "full")


async def _technicals(source: MarketDataSource, symbol: str, as_of: date | None):
    history = await source.get_price_history(symbol, "2y", "1d", as_of)
    if history is None or not history.bars:
        return None
    return compute_technicals(history)


async def build_dossier(
    source: MarketDataSource,
    symbol: str,
    depth: str = "full",
    as_of: date | None = None,
) -> CompanyDossier:
    """Build a consolidated dossier. ``depth='summary'`` is snapshot-only; ``'full'`` adds
    fundamentals, dividends, technicals, earnings, analyst view and news — all concurrently.
    Partial failures land in ``notes`` instead of failing the whole call."""
    if depth not in DEPTHS:
        raise ValueError(f"depth must be one of {DEPTHS}.")

    clean_symbol = symbol.strip().upper()
    labels = ["snapshot"]
    coroutines = [source.get_snapshot(clean_symbol, as_of)]
    if depth == "full":
        labels += ["fundamentals", "dividends", "technicals", "earnings", "analyst", "news"]
        coroutines += [
            source.get_fundamentals(clean_symbol, Period.ANNUAL, as_of),
            source.get_dividends(clean_symbol, as_of),
            _technicals(source, clean_symbol, as_of),
            source.get_earnings(clean_symbol, as_of),
            source.get_analyst_view(clean_symbol),
            source.get_news(clean_symbol, 8),
        ]

    results = await asyncio.gather(*coroutines, return_exceptions=True)
    resolved: dict[str, object | None] = {}
    notes: list[str] = []
    for label, result in zip(labels, results, strict=True):
        if isinstance(result, Exception):
            notes.append(f"{label} unavailable: {result}")
            resolved[label] = None
        else:
            resolved[label] = result

    if resolved.get("snapshot") is None and "snapshot unavailable" not in " ".join(notes):
        notes.append(f"{clean_symbol} could not be resolved to a snapshot.")

    return CompanyDossier(
        symbol=clean_symbol,
        as_of=as_of,
        snapshot=resolved.get("snapshot"),
        fundamentals=resolved.get("fundamentals"),
        dividends=resolved.get("dividends"),
        technicals=resolved.get("technicals"),
        earnings=resolved.get("earnings"),
        analyst=resolved.get("analyst"),
        news=resolved.get("news"),
        notes=notes,
    )
