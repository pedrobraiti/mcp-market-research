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
from decimal import Decimal, InvalidOperation
from typing import Any

from ...domain.models import Filing, FilingsList, SecFinancialLine, SecFinancials

_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{document}"
_CONCEPT_URL = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"

# Each metric maps to the us-gaap tags companies actually use, tried in order until one hits
# (different filers tag the same line differently; the first that returns data wins).
_CONCEPTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "revenue",
        (
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues",
            "RevenueFromContractWithCustomerIncludingAssessedTax",
            "SalesRevenueNet",
        ),
    ),
    ("gross_profit", ("GrossProfit",)),
    ("operating_income", ("OperatingIncomeLoss",)),
    ("net_income", ("NetIncomeLoss",)),
    ("total_assets", ("Assets",)),
    (
        "stockholders_equity",
        (
            "StockholdersEquity",
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        ),
    ),
)


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _pick_annual(observations: list[dict], as_of: date | None) -> dict | None:
    """Pick the latest full-year (FY, 10-K) observation at or before ``as_of``."""
    best: dict | None = None
    best_key: tuple[date, date] | None = None
    for entry in observations:
        if str(entry.get("fp")) != "FY":
            continue
        if not str(entry.get("form", "")).startswith("10-K"):
            continue
        period_end = _parse_date(entry.get("end"))
        if period_end is None or (as_of is not None and period_end > as_of):
            continue
        # Break ties (same period restated by an amendment) by the later filing date.
        filed = _parse_date(entry.get("filed")) or date.min
        key = (period_end, filed)
        if best_key is None or key > best_key:
            best, best_key = entry, key
    return best


class SecEdgar:
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

    async def get_financials(
        self, symbol: str, as_of: date | None = None
    ) -> SecFinancials | None:
        symbol_upper = symbol.strip().upper()
        cik = (await self._ticker_map()).get(symbol_upper)
        if cik is None:
            return None

        results = await asyncio.gather(
            *(self._concept_line(cik, concept, tags, as_of) for concept, tags in _CONCEPTS),
            return_exceptions=True,
        )
        lines = [line for line in results if isinstance(line, SecFinancialLine)]
        # Anchor the snapshot's fiscal year on a core line (net income, else the first with data).
        anchor = next(
            (line for line in lines if line.concept == "net_income" and line.value is not None),
            next((line for line in lines if line.value is not None), None),
        )
        return SecFinancials(
            symbol=symbol_upper,
            cik=cik,
            fiscal_year=anchor.fiscal_year if anchor else None,
            period_end=anchor.period_end if anchor else None,
            lines=lines,
            as_of=as_of,
        )

    async def _concept_line(
        self, cik: str, concept: str, tags: tuple[str, ...], as_of: date | None
    ) -> SecFinancialLine:
        for tag in tags:
            try:
                data = await self._fetch_json(_CONCEPT_URL.format(cik=cik, tag=tag))
            except Exception:  # noqa: BLE001 — a 404 just means this filer doesn't use the tag
                continue
            observations = ((data or {}).get("units") or {}).get("USD") or []
            entry = _pick_annual(observations, as_of)
            if entry is None:
                continue
            return SecFinancialLine(
                concept=concept,
                tag=tag,
                value=_to_decimal(entry.get("val")),
                unit="USD",
                period_end=_parse_date(entry.get("end")),
                fiscal_year=entry.get("fy") if isinstance(entry.get("fy"), int) else None,
                form=entry.get("form"),
                filed=_parse_date(entry.get("filed")),
            )
        return SecFinancialLine(concept=concept, value=None)
