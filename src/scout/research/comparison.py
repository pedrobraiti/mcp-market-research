"""``compare`` — several symbols side by side, gathered in parallel.

Pure aggregation over the market-data port: per symbol it pulls a snapshot and the latest
fundamentals concurrently, and assembles one comparable row. A symbol whose data is missing
gets a row with a note rather than dropping out.
"""

from __future__ import annotations

import asyncio
from datetime import date

from ..domain.models import Comparison, ComparisonRow, Period
from ..domain.ports import MarketDataSource


async def build_comparison(
    source: MarketDataSource, symbols: list[str], as_of: date | None = None
) -> Comparison:
    clean = [s.strip().upper() for s in symbols if s.strip()]

    async def _row(symbol: str) -> ComparisonRow:
        snapshot, fundamentals = await asyncio.gather(
            source.get_snapshot(symbol, as_of),
            source.get_fundamentals(symbol, Period.ANNUAL, as_of),
            return_exceptions=True,
        )
        snap = snapshot if not isinstance(snapshot, Exception) else None
        fund = fundamentals if not isinstance(fundamentals, Exception) else None
        if snap is None and fund is None:
            return ComparisonRow(symbol=symbol, note="data unavailable")
        return ComparisonRow(
            symbol=symbol,
            name=snap.name if snap else None,
            price=snap.price if snap else None,
            market_cap=snap.market_cap if snap else None,
            pe_ratio=snap.pe_ratio if snap else None,
            forward_pe=snap.forward_pe if snap else None,
            dividend_yield=snap.dividend_yield if snap else None,
            revenue=fund.revenue if fund else None,
            net_margin=fund.net_margin if fund else None,
            sector=snap.sector if snap else None,
        )

    rows = await asyncio.gather(*(_row(symbol) for symbol in clean))
    return Comparison(symbols=clean, as_of=as_of, rows=list(rows))
