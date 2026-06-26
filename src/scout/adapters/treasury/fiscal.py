"""US Treasury Fiscal Data API implementation — keyless, no account required.

Official US government figures: total public debt outstanding and the average interest rate the
Treasury pays by security type. Authoritative and free; complements FRED with primary fiscal data.

The JSON fetch is injected for offline tests.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from ...domain.models import TreasuryData, TreasuryFigure

_BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"
_DEBT_URL = _BASE + "v2/accounting/od/debt_to_penny?sort=-record_date&page[size]=1"
_RATES_URL = _BASE + "v2/accounting/od/avg_interest_rates?sort=-record_date&page[size]=30"


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


class TreasuryFiscal:
    def __init__(
        self,
        fetch_json: Callable[[str], Awaitable[dict]] | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._timeout = timeout
        self._fetch_json = fetch_json or self._default_fetch_json

    async def _default_fetch_json(self, url: str) -> dict:
        import httpx

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_data(self) -> TreasuryData:
        debt_data, rates_data = await asyncio.gather(
            self._fetch_json(_DEBT_URL), self._fetch_json(_RATES_URL), return_exceptions=True
        )
        figures: list[TreasuryFigure] = []

        debt_rows = (debt_data or {}).get("data") or [] if isinstance(debt_data, dict) else []
        if debt_rows:
            row = debt_rows[0]
            figures.append(
                TreasuryFigure(
                    name="Total public debt outstanding",
                    value=_dec(row.get("tot_pub_debt_out_amt")),
                    unit="USD",
                    record_date=_parse_date(row.get("record_date")),
                )
            )

        rate_rows = (rates_data or {}).get("data") or [] if isinstance(rates_data, dict) else []
        if rate_rows:
            latest = rate_rows[0].get("record_date")
            for row in rate_rows:
                if row.get("record_date") != latest:
                    continue
                figures.append(
                    TreasuryFigure(
                        name=f"Avg interest rate — {row.get('security_desc')}",
                        value=_dec(row.get("avg_interest_rate_amt")),
                        unit="%",
                        record_date=_parse_date(latest),
                    )
                )
        return TreasuryData(figures=figures)
