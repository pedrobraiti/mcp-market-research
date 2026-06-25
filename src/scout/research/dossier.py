"""``company_dossier`` — fan several reads out in parallel and consolidate.

This is the embodiment of the "fat, purposeful tool with internal parallelism" principle:
one call, several sources gathered concurrently with ``asyncio.gather``, returned as one
structured object. A failure in one read becomes a note, not a total failure.
"""

from __future__ import annotations

import asyncio
from datetime import date

from ..domain.models import CompanyDossier, Period
from ..domain.ports import MarketDataSource

DEPTHS = ("summary", "full")


async def build_dossier(
    source: MarketDataSource,
    symbol: str,
    depth: str = "full",
    as_of: date | None = None,
) -> CompanyDossier:
    """Build a consolidated dossier. ``depth='summary'`` is snapshot-only; ``'full'`` adds
    fundamentals and dividends. Reads run concurrently; partial failures land in ``notes``."""
    if depth not in DEPTHS:
        raise ValueError(f"depth must be one of {DEPTHS}.")

    clean_symbol = symbol.strip().upper()
    labels = ["snapshot"]
    coroutines = [source.get_snapshot(clean_symbol, as_of)]
    if depth == "full":
        labels += ["fundamentals", "dividends"]
        coroutines += [
            source.get_fundamentals(clean_symbol, Period.ANNUAL, as_of),
            source.get_dividends(clean_symbol, as_of),
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
        notes=notes,
    )
