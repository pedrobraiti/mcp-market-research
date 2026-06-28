"""World Bank Indicators API implementation — keyless, no API key.

Country-level macro (GDP growth, inflation, unemployment, GDP per capita, population). Broadens
the MCP beyond US-only (the broker can reach non-US assets, and the data is official). Lower
frequency than FRED — this is structural/annual context, not a trading-day signal.

The JSON fetch is injected for offline tests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from decimal import Decimal, InvalidOperation
from typing import Any

from ...domain.models import WorldBankData, WorldBankIndicator

_URL = "https://api.worldbank.org/v2/country/{country}/indicator/{code}?format=json&mrv=5"

_DEFAULT_INDICATORS: tuple[tuple[str, str], ...] = (
    ("NY.GDP.MKTP.KD.ZG", "GDP growth (annual %)"),
    ("FP.CPI.TOTL.ZG", "Inflation, consumer prices (annual %)"),
    ("SL.UEM.TOTL.ZS", "Unemployment (% of labour force)"),
    ("NY.GDP.PCAP.CD", "GDP per capita (current US$)"),
    ("SP.POP.TOTL", "Population, total"),
)


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _year(value: Any) -> int | None:
    try:
        return int(str(value)[:4])
    except (TypeError, ValueError):
        return None


class WorldBankMacro:
    def __init__(
        self,
        fetch_json: Callable[[str], Awaitable[Any]] | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._timeout = timeout
        self._fetch_json = fetch_json or self._default_fetch_json

    async def _default_fetch_json(self, url: str) -> Any:
        import httpx

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_indicators(
        self, country: str = "USA", codes: list[str] | None = None
    ) -> WorldBankData:
        clean_country = country.strip().upper() or "USA"
        targets = [(c, c) for c in codes] if codes else list(_DEFAULT_INDICATORS)
        # Sequential, not parallel: the World Bank API rate-limits concurrent requests, which
        # would silently drop indicators. This is low-frequency macro, so latency is fine.
        indicators: list[WorldBankIndicator] = []
        for code, name in targets:
            try:
                indicators.append(await self._one(clean_country, code, name))
            except Exception:  # noqa: BLE001 — skip an indicator that fails, keep the rest
                continue
        # Some requested indicators were dropped → the set is thinner than asked for; flag it so
        # the caller doesn't read a missing indicator as "this country has no such data".
        partial = len(indicators) < len(targets)
        return WorldBankData(country=clean_country, indicators=indicators, partial=partial)

    async def _one(self, country: str, code: str, fallback_name: str) -> WorldBankIndicator:
        data = await self._fetch_json(_URL.format(country=country, code=code))
        observations = data[1] if isinstance(data, list) and len(data) >= 2 else []
        if isinstance(observations, list):
            for entry in observations:  # mrv returns newest-first
                if not isinstance(entry, dict) or entry.get("value") is None:
                    continue
                indicator_name = (entry.get("indicator") or {}).get("value")
                return WorldBankIndicator(
                    code=code,
                    name=indicator_name or fallback_name,
                    value=_dec(entry.get("value")),
                    year=_year(entry.get("date")),
                    country=entry.get("countryiso3code") or country,
                )
        return WorldBankIndicator(code=code, name=fallback_name, country=country)
