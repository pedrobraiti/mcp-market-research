"""FRED implementation of ``MacroSource``.

Uses FRED's keyless ``fredgraph.csv`` download endpoint, so no API key is required — it stays in
the "free sources first" spirit. Each series is fetched concurrently; a series that fails is
dropped from the snapshot rather than failing the whole call.

The CSV fetch is injected (``fetch_csv``) so the unit tests run fully offline.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from ...analytics import (
    percentile_of_last,
    recession_probit,
    sahm_gap,
    trailing_negative_run,
    zscore_of_last,
)
from ...domain.models import MacroDerived, MacroIndicator, MacroSnapshot
from ..retry import SourceUnavailable, with_retry

_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"

# (series id, human label). Chosen for an equity macro read: policy rate, the curve,
# the labour market, inflation level and volatility. DGS3MO feeds the recession probit.
_SERIES: tuple[tuple[str, str], ...] = (
    ("FEDFUNDS", "Federal Funds Rate (%)"),
    ("DGS10", "10-Year Treasury Yield (%)"),
    ("DGS2", "2-Year Treasury Yield (%)"),
    ("DGS3MO", "3-Month Treasury Yield (%)"),
    ("T10Y2Y", "10Y-2Y Treasury Spread (%)"),
    ("UNRATE", "Unemployment Rate (%)"),
    ("CPIAUCSL", "CPI (index, SA)"),
    ("VIXCLS", "VIX (volatility index)"),
)

_VIX_WINDOW = 252  # ~1 trading year for the VIX regime z-score/percentile
_CPI_YOY_MIN_MONTHS = 13  # need a year-ago observation to compute YoY


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


def _observations(csv_text: str, as_of: date | None) -> list[tuple[date, Decimal]]:
    """Parse a fredgraph CSV into (date, value) pairs at or before ``as_of``, oldest→newest.
    Missing observations (FRED's dot) are skipped. The whole series is kept — not just the last
    point — so the derived layer can compute YoY, z-scores, the Sahm gap, etc."""
    rows: list[tuple[date, Decimal]] = []
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
        rows.append((observation_date, value))
    rows.sort(key=lambda r: r[0])
    return rows


def _value_on_or_before(obs: list[tuple[date, Decimal]], target: date) -> Decimal | None:
    """Most recent value at or before ``target`` (obs assumed oldest→newest)."""
    result: Decimal | None = None
    for observation_date, value in obs:
        if observation_date <= target:
            result = value
        else:
            break
    return result


def _round(value: float | None, places: int) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(round(value, places)))


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
        indicators: list[MacroIndicator] = []
        series: dict[str, list[tuple[date, Decimal]]] = {}
        for result in results:
            if not isinstance(result, tuple):
                continue  # a genuine fetch error → that series is dropped, as before
            indicator, observations = result
            indicators.append(indicator)
            if observations:
                series[indicator.series_id] = observations
        return MacroSnapshot(
            indicators=indicators, derived=_derive(series), as_of=as_of
        )

    async def _one(
        self, series_id: str, name: str, as_of: date | None
    ) -> tuple[MacroIndicator, list[tuple[date, Decimal]] | None]:
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
            indicator = MacroIndicator(
                series_id=series_id, name=name, value=None, status=exc.status
            )
            return indicator, None
        observations = _observations(csv_text, as_of)
        latest_date, latest_value = observations[-1] if observations else (None, None)
        indicator = MacroIndicator(
            series_id=series_id, name=name, value=latest_value, observation_date=latest_date
        )
        return indicator, observations


def _derive(series: dict[str, list[tuple[date, Decimal]]]) -> MacroDerived:
    """Turn the raw FRED series into regime metrics. Every block is independently guarded so a
    missing or short series simply leaves its fields null (and, where useful, leaves a note)."""
    derived = MacroDerived()
    notes: list[str] = []

    cpi = series.get("CPIAUCSL")
    cpi_yoy: float | None = None
    if cpi and len(cpi) >= _CPI_YOY_MIN_MONTHS:
        latest_date, latest_value = cpi[-1]
        year_ago = _value_on_or_before(cpi, latest_date - timedelta(days=365))
        if year_ago and year_ago != 0:
            cpi_yoy = (float(latest_value) / float(year_ago) - 1) * 100
            derived.cpi_yoy = _round(cpi_yoy, 2)
    if cpi and len(cpi) >= 4:
        latest_date, latest_value = cpi[-1]
        three_ago = _value_on_or_before(cpi, latest_date - timedelta(days=92))
        if three_ago and three_ago != 0:
            derived.cpi_3m_annualized = _round(
                ((float(latest_value) / float(three_ago)) ** 4 - 1) * 100, 2
            )

    if cpi_yoy is not None:
        fedfunds = series.get("FEDFUNDS")
        if fedfunds:
            derived.real_fed_funds = _round(float(fedfunds[-1][1]) - cpi_yoy, 2)
        dgs10 = series.get("DGS10")
        if dgs10:
            derived.real_10y = _round(float(dgs10[-1][1]) - cpi_yoy, 2)

    unrate = series.get("UNRATE")
    if unrate:
        gap = sahm_gap([float(v) for _, v in unrate])
        if gap is not None:
            derived.sahm_gap = _round(gap, 2)
            derived.sahm_recession_signal = gap >= 0.50

    vix = series.get("VIXCLS")
    if vix and len(vix) >= 30:
        window = [float(v) for _, v in vix][-_VIX_WINDOW:]
        z = zscore_of_last(window)
        pct = percentile_of_last(window)
        derived.vix_zscore = _round(z, 2)
        derived.vix_percentile = _round(pct * 100, 1) if pct is not None else None

    t10y2y = series.get("T10Y2Y")
    if t10y2y:
        spread_values = [float(v) for _, v in t10y2y]
        derived.yield_curve_inverted = spread_values[-1] < 0
        derived.yield_curve_days_inverted = trailing_negative_run(spread_values)

    dgs10 = series.get("DGS10")
    dgs3mo = series.get("DGS3MO")
    if dgs10 and dgs3mo:
        spread = float(dgs10[-1][1]) - float(dgs3mo[-1][1])
        derived.recession_prob_12m = _round(recession_probit(spread) * 100, 1)
        notes.append(
            "recession_prob_12m: NY-Fed probit on the latest daily 10y-3m spread as a proxy for "
            "the model's monthly-average input."
        )

    derived.notes = notes
    return derived
