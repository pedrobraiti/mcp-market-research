"""Batch aggregators — one call over a list of symbols, returning an aggregated view.

These exist because portfolio monitoring asks "across my N positions…", which a per-symbol
loop answers poorly (N round-trips, no consolidated/sorted result). Each fans the relevant
per-symbol port read out in parallel and consolidates. Stateless: the agent passes the list
every time; Scout remembers nothing.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime

from ..domain.models import (
    CalendarEvent,
    Classification,
    ClassificationItem,
    DigestNewsItem,
    MarketCalendar,
    NewsDigest,
)
from ..domain.ports import MarketDataSource

_EPOCH = datetime(1970, 1, 1)


def _clean(symbols: list[str]) -> list[str]:
    return [s.strip().upper() for s in symbols if s.strip()]


async def build_classification(
    source: MarketDataSource, symbols: list[str], as_of: date | None = None
) -> Classification:
    clean = _clean(symbols)
    snapshots = await asyncio.gather(
        *(source.get_snapshot(s, as_of) for s in clean), return_exceptions=True
    )
    items: list[ClassificationItem] = []
    for symbol, snap in zip(clean, snapshots, strict=False):
        if isinstance(snap, Exception) or snap is None:
            items.append(ClassificationItem(symbol=symbol, note="unavailable"))
            continue
        items.append(
            ClassificationItem(
                symbol=symbol,
                name=snap.name,
                sector=snap.sector,
                industry=snap.industry,
                market_cap=snap.market_cap,
            )
        )
    return Classification(items=items, as_of=as_of)


async def build_news_digest(
    source: MarketDataSource, symbols: list[str], limit_per_symbol: int = 5
) -> NewsDigest:
    clean = _clean(symbols)
    results = await asyncio.gather(
        *(source.get_news(s, limit_per_symbol) for s in clean), return_exceptions=True
    )
    items: list[DigestNewsItem] = []
    notes: list[str] = []
    for symbol, result in zip(clean, results, strict=False):
        if isinstance(result, Exception) or result is None:
            notes.append(f"{symbol}: news unavailable")
            continue
        for news_item in result.items:
            items.append(
                DigestNewsItem(
                    symbol=symbol,
                    title=news_item.title,
                    publisher=news_item.publisher,
                    published=news_item.published,
                    url=news_item.url,
                )
            )
    items.sort(key=lambda i: i.published or _EPOCH, reverse=True)
    return NewsDigest(symbols=clean, items=items, notes=notes)


async def build_calendar(
    source: MarketDataSource, symbols: list[str], as_of: date | None = None
) -> MarketCalendar:
    clean = _clean(symbols)
    reference = as_of or date.today()
    earnings, dividends = await asyncio.gather(
        asyncio.gather(*(source.get_earnings(s, as_of) for s in clean), return_exceptions=True),
        asyncio.gather(*(source.get_dividends(s, as_of) for s in clean), return_exceptions=True),
    )

    events: list[CalendarEvent] = []
    notes: list[str] = []
    for symbol, result in zip(clean, earnings, strict=False):
        if isinstance(result, Exception) or result is None:
            notes.append(f"{symbol}: earnings unavailable")
        elif result.next_earnings_date and result.next_earnings_date >= reference:
            events.append(
                CalendarEvent(symbol=symbol, type="earnings", date=result.next_earnings_date)
            )
    for symbol, result in zip(clean, dividends, strict=False):
        if isinstance(result, Exception) or result is None:
            continue
        if result.next_ex_dividend and result.next_ex_dividend >= reference:
            events.append(
                CalendarEvent(symbol=symbol, type="ex_dividend", date=result.next_ex_dividend)
            )

    events.sort(key=lambda e: e.date)
    return MarketCalendar(symbols=clean, events=events, notes=notes)
