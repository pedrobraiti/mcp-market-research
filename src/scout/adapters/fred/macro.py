"""FRED implementation of ``MacroSource``.

Uses FRED's keyless ``fredgraph.csv`` download endpoint, so no API key is required — it stays in
the "free sources first" spirit. Each series is fetched concurrently; a series that fails is
dropped from the snapshot rather than failing the whole call.

The CSV fetch is injected (``fetch_csv``) so the unit tests run fully offline.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ...domain.models import MacroIndicator, MacroSnapshot
from ..retry import SourceUnavailable, with_retry

_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"

# (series id, human label). Chosen for an equity macro read: policy rate, the curve,
# the labour market, inflation level and volatility.
_SERIES: tuple[tuple[str, str], ...] = (
    ("FEDFUNDS", "Federal Funds Rate (%)"),
    ("DGS10", "10-Year Treasury Yield (%)"),
    ("DGS2", "2-Year Treasury Yield (%)"),
    ("T10Y2Y", "10Y-2Y Treasury Spread (%)"),
    ("UNRATE", "Unemployment Rate (%)"),
    ("CPIAUCSL", "CPI (index, SA)"),
    ("VIXCLS", "VIX (volatility index)"),
)


def _parse_value(raw: str) -> Decimal | None:
    raw = raw.strip()
    if not raw or raw == ".":  # FRED marks missing observations with a dot
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def _parse_date(raw: str) -> date | None:
    try:
        return datetime.strptime(raw.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _latest(csv_text: str, as_of: date | None) -> tuple[Decimal | None, date | None]:
    """Return the most recent (value, date) at or before ``as_of`` from a fredgraph CSV."""
    best_value: Decimal | None = None
    best_date: date | None = None
    for line in csv_text.splitlines()[1:]:  # skip the header row
        parts = line.split(",")
        if len(parts) < 2:
            continue
        observation_date = _parse_date(parts[0])
        value = _parse_value(parts[1])
        if observation_date is None or value is None:
            continue
        if as_of is not None and observation_date > as_of:
            continue
        if best_date is None or observation_date > best_date:
            best_date, best_value = observation_date, value
    return best_value, best_date


class FredMacro:
    def __init__(
        self,
        fetch_csv: Callable[[str], Awaitable[str]] | None = None,
        timeout: float = 15.0,
        retry_attempts: int = 3,
        retry_base_delay: float = 0.5,
    ) -> None:
        self._timeout = timeout
        self._retry_attempts = retry_attempts
        self._retry_base_delay = retry_base_delay
        self._fetch_csv = fetch_csv or self._default_fetch_csv

    async def _default_fetch_csv(self, url: str) -> str:
        import httpx

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    async def get_macro_context(self, as_of: date | None = None) -> MacroSnapshot:
        results = await asyncio.gather(
            *(self._one(series_id, name, as_of) for series_id, name in _SERIES),
            return_exceptions=True,
        )
        indicators = [r for r in results if isinstance(r, MacroIndicator)]
        return MacroSnapshot(indicators=indicators, as_of=as_of)

    async def _one(self, series_id: str, name: str, as_of: date | None) -> MacroIndicator:
        url = _CSV_URL.format(series=series_id)
        try:
            csv_text = await with_retry(
                lambda: self._fetch_csv(url),
                attempts=self._retry_attempts,
                base_delay=self._retry_base_delay,
            )
        except SourceUnavailable as exc:
            # Keep the series in the snapshot but flag it: a rate-limited/timed-out series must
            # not vanish (which would read as "no such indicator") — value is null WITH a status.
            return MacroIndicator(series_id=series_id, name=name, value=None, status=exc.status)
        value, observation_date = _latest(csv_text, as_of)
        return MacroIndicator(
            series_id=series_id, name=name, value=value, observation_date=observation_date
        )
