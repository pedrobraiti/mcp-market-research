"""SEC EDGAR implementation of ``FilingsSource``.

EDGAR is free and authoritative — the primary source filings cross-check yfinance against.
It requires an identifiable ``User-Agent`` (SEC policy) and is rate-limited to ~10 req/s.

The HTTP layer is injected via ``fetch_json`` (a callable ``url -> dict``), imported lazily
only when the default httpx-based fetcher is used, so the unit tests run fully offline.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from typing import Any

from ...domain.models import Filing, FilingsList

_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{document}"


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


class SecEdgarFilings:
    def __init__(
        self,
        user_agent: str,
        fetch_json: Callable[[str], Awaitable[dict]] | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._user_agent = user_agent
        self._timeout = timeout
        self._fetch_json = fetch_json or self._default_fetch_json
        self._cik_by_ticker: dict[str, str] | None = None
        self._lock = asyncio.Lock()

    async def _default_fetch_json(self, url: str) -> dict:
        import httpx  # imported lazily so offline tests never need httpx or the network

        headers = {"User-Agent": self._user_agent, "Accept-Encoding": "gzip, deflate"}
        async with httpx.AsyncClient(timeout=self._timeout, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def _ticker_map(self) -> dict[str, str]:
        if self._cik_by_ticker is None:
            async with self._lock:
                if self._cik_by_ticker is None:
                    data = await self._fetch_json(_TICKERS_URL)
                    rows = data.values() if isinstance(data, dict) else data
                    mapping: dict[str, str] = {}
                    for row in rows:
                        ticker = str(row.get("ticker", "")).upper()
                        cik = str(row.get("cik_str") or row.get("cik") or "").zfill(10)
                        if ticker and cik != "0000000000":
                            mapping[ticker] = cik
                    self._cik_by_ticker = mapping
        return self._cik_by_ticker

    async def get_filings(
        self,
        symbol: str,
        form_type: str | None = None,
        limit: int = 20,
        as_of: date | None = None,
    ) -> FilingsList | None:
        symbol_upper = symbol.strip().upper()
        cik = (await self._ticker_map()).get(symbol_upper)
        if cik is None:
            return None

        data = await self._fetch_json(_SUBMISSIONS_URL.format(cik=cik))
        recent = ((data or {}).get("filings") or {}).get("recent") or {}
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        accessions = recent.get("accessionNumber", [])
        documents = recent.get("primaryDocument", [])
        descriptions = recent.get("primaryDocDescription", [])

        wanted = form_type.strip().upper() if form_type else None
        cik_int = str(int(cik))
        capped = max(1, min(limit, 100))
        results: list[Filing] = []
        for i, form in enumerate(forms):  # arrays are newest-first
            if wanted and str(form).upper() != wanted:
                continue
            filing_date = _parse_date(filing_dates[i]) if i < len(filing_dates) else None
            if filing_date is None or (as_of is not None and filing_date > as_of):
                continue
            accession = accessions[i] if i < len(accessions) else ""
            document = documents[i] if i < len(documents) else None
            url = None
            if accession and document:
                url = _ARCHIVE_URL.format(
                    cik_int=cik_int, accession=accession.replace("-", ""), document=document
                )
            results.append(
                Filing(
                    form=str(form),
                    filing_date=filing_date,
                    report_date=_parse_date(report_dates[i]) if i < len(report_dates) else None,
                    accession=accession,
                    primary_document=document,
                    description=descriptions[i] if i < len(descriptions) else None,
                    url=url,
                )
            )
            if len(results) >= capped:
                break

        return FilingsList(
            symbol=symbol_upper, cik=cik, name=(data or {}).get("name"), filings=results
        )
