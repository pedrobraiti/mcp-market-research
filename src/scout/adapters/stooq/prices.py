"""stooq price history — keyless daily OHLCV via CSV download.

stooq has no real API, but exposes daily OHLCV as a CSV download with no key. It's used as a
**fallback** for price history when yfinance (a scraper) fails or rate-limits — resilience, not a
new signal. Daily only; intraday returns ``None`` so the caller keeps the primary source's result.

The CSV fetch is injected for offline tests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import date, datetime, timedelta

from ...domain.models import PriceBar, PriceHistory

_CSV_URL = "https://stooq.com/q/d/l/?s={symbol}.us&i=d"

# Approximate calendar days per range token.
_RANGE_DAYS = {
    "1mo": 31, "3mo": 93, "6mo": 186, "1y": 366, "2y": 731,
    "5y": 1827, "10y": 3653, "ytd": 366, "max": 100_000,
}


def _to_decimal(value: str):
    from decimal import Decimal, InvalidOperation

    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def _parse(symbol: str, csv_text: str, range_: str, as_of: date | None) -> PriceHistory | None:
    lines = csv_text.strip().splitlines()
    if len(lines) < 2 or not lines[0].lower().startswith("date"):
        return None
    end = as_of or date.today()
    start = end - timedelta(days=_RANGE_DAYS.get(range_, 186))
    bars: list[PriceBar] = []
    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) < 6:
            continue
        try:
            bar_date = datetime.strptime(parts[0], "%Y-%m-%d").date()
        except ValueError:
            continue
        if bar_date < start or bar_date > end:
            continue
        volume = parts[5].strip()
        bars.append(
            PriceBar(
                date=bar_date,
                open=_to_decimal(parts[1]),
                high=_to_decimal(parts[2]),
                low=_to_decimal(parts[3]),
                close=_to_decimal(parts[4]),
                volume=int(volume) if volume.isdigit() else None,
            )
        )
    if not bars:
        return None
    return PriceHistory(symbol=symbol, interval="1d", bars=bars, as_of=as_of)


class StooqPrices:
    def __init__(
        self,
        fetch_csv: Callable[[str], Awaitable[str]] | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._timeout = timeout
        self._fetch_csv = fetch_csv or self._default_fetch_csv

    async def _default_fetch_csv(self, url: str) -> str:
        import httpx

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        }
        async with httpx.AsyncClient(
            timeout=self._timeout, headers=headers, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    async def get_price_history(
        self, symbol: str, range: str = "6mo", interval: str = "1d", as_of: date | None = None
    ) -> PriceHistory | None:
        if interval != "1d":  # stooq's keyless CSV is daily only
            return None
        clean = symbol.strip().lower()
        text = await self._fetch_csv(_CSV_URL.format(symbol=clean))
        return _parse(symbol.strip().upper(), text, range, as_of)
