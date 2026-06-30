"""CFTC Commitments of Traders implementation — keyless Socrata, no API key, no auth.

The CFTC publishes the weekly Commitments of Traders (COT) report — futures positioning split by
trader class (large speculators vs commercials/hedgers) — on a public Socrata endpoint. This adds
the positioning dimension Scout otherwise lacks: ``net`` = long − short tells you whether the
"smart money" (commercials) and the trend-followers (speculators) are crowded one way.

The legacy futures-only dataset (``jun7-fc8e``) is used for breadth: it covers every reporting
market (metals, energy, grains, FX, equity-index, rates…) in one place. Positions are as of the
Tuesday and published the following Friday (~3-day lag), so a report is a point-in-time settlement
snapshot, never "today".

One keyless GET per call (SoQL via query params); the JSON fetch is injected for offline tests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlencode

from ...analytics import zscore_of_last
from ...domain.models import CotReport, CotWeek
from ..retry import SourceUnavailable, with_retry

_BASE = "https://publicreporting.cftc.gov/resource/jun7-fc8e.json"
_DATE_FIELD = "report_date_as_yyyy_mm_dd"
_MAX_WEEKS = 52
_MIN_WEEKS_FOR_ZSCORE = 8  # a z-score below this many points is too noisy to report
# Each matched market needs its own ``weeks`` rows in a single date-ordered fetch; a generous
# multiplier (capped) keeps it one request even when the query matches several markets.
_FETCH_MULTIPLIER = 30
_FETCH_CAP = 1500


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return None if result.is_nan() else result


def _int(value: Any) -> int | None:
    decimal_value = _dec(value)
    return int(decimal_value) if decimal_value is not None else None


def _parse_date(value: Any) -> date | None:
    """Take the date out of an ISO datetime string (the Socrata field is a full timestamp)."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except ValueError:
            return None


def _quantize(value: Decimal | None, places: int) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)


def _diff(a: Decimal | None, b: Decimal | None) -> Decimal | None:
    return None if a is None or b is None else a - b


_LAG_NOTE = (
    "Weekly CFTC COT (legacy futures-only). Positions are as of the Tuesday and published the "
    "following Friday (~3-day lag); as_of is the report's settlement date, not today."
)


class CftcPositioning:
    def __init__(
        self,
        fetch_json: Callable[[str], Awaitable[Any]] | None = None,
        timeout: float = 15.0,
        retry_attempts: int = 3,
        retry_base_delay: float = 0.5,
    ) -> None:
        self._timeout = timeout
        self._retry_attempts = retry_attempts
        self._retry_base_delay = retry_base_delay
        self._fetch_json = fetch_json or self._default_fetch_json

    async def _default_fetch_json(self, url: str) -> Any:
        import httpx

        headers = {"User-Agent": "scout-mcp/0.1 (research; +https://github.com/pedrobraiti)"}
        async with httpx.AsyncClient(timeout=self._timeout, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            if not response.text.strip():
                return []
            return response.json()

    async def get_positioning(self, market: str, weeks: int = 12) -> CotReport:
        clean = market.strip()
        window = max(1, min(weeks, _MAX_WEEKS))
        # Socrata SoQL: case-insensitive substring on the market name, newest first.
        escaped = clean.replace("'", "''")
        params = {
            "$where": f"upper(market_and_exchange_names) like '%{escaped.upper()}%'",
            "$order": f"{_DATE_FIELD} DESC",
            "$limit": min(window * _FETCH_MULTIPLIER, _FETCH_CAP),
        }
        url = f"{_BASE}?{urlencode(params)}"
        try:
            data = await with_retry(
                lambda: self._fetch_json(url),
                attempts=self._retry_attempts,
                base_delay=self._retry_base_delay,
            )
        except SourceUnavailable as exc:
            # A 429/timeout is "couldn't fetch", NOT "no such market" — surface it so a downstream
            # gate retries/abstains instead of reading an empty result as a real absence.
            return CotReport(market=clean, source_status=exc.status)

        rows = [row for row in data if isinstance(row, dict)] if isinstance(data, list) else []
        groups: dict[str, list[dict]] = {}
        for row in rows:
            name = row.get("market_and_exchange_names")
            if isinstance(name, str) and name.strip():
                groups.setdefault(name.strip(), []).append(row)
        if not groups:
            return CotReport(
                market=clean,
                note=f"No CFTC COT market matched '{clean}'. Try a broader name, e.g. 'GOLD'.",
            )

        # Rows arrive newest-first, so the first row per group is its latest report. The primary
        # series is the match with the highest latest open interest — don't silently pick a thin
        # micro-contract when the headline market is what the caller meant.
        def latest_open_interest(market_rows: list[dict]) -> Decimal:
            return _dec(market_rows[0].get("open_interest_all")) or Decimal(0)

        primary_name = max(groups, key=lambda name: latest_open_interest(groups[name]))
        primary_rows = groups[primary_name]
        latest = primary_rows[0]

        history = [_week(row) for row in primary_rows[:window]]
        history = [week for week in history if week is not None]
        history.sort(key=lambda week: week.report_date)  # oldest → newest

        net_series = [float(week.noncomm_net) for week in history if week.noncomm_net is not None]
        zscore = (
            _dec(zscore_of_last(net_series)) if len(net_series) >= _MIN_WEEKS_FOR_ZSCORE else None
        )

        noncomm_long = _dec(latest.get("noncomm_positions_long_all"))
        noncomm_short = _dec(latest.get("noncomm_positions_short_all"))
        comm_long = _dec(latest.get("comm_positions_long_all"))
        comm_short = _dec(latest.get("comm_positions_short_all"))
        open_interest = _dec(latest.get("open_interest_all"))
        noncomm_net = _diff(noncomm_long, noncomm_short)
        comm_net = _diff(comm_long, comm_short)
        pct_oi = (
            noncomm_net / open_interest * Decimal(100)
            if noncomm_net is not None and open_interest and open_interest > 0
            else None
        )
        net_change = _diff(
            _dec(latest.get("change_in_noncomm_long_all")),
            _dec(latest.get("change_in_noncomm_short_all")),
        )

        others = sorted(name for name in groups if name != primary_name)
        note = _LAG_NOTE
        if others:
            note += (
                f" '{clean}' also matched {len(others)} other market(s) "
                f"(focused on the highest-open-interest one): {', '.join(others)}."
            )

        return CotReport(
            market=clean,
            market_name=primary_name,
            commodity_name=latest.get("commodity_name"),
            contract_market_name=latest.get("contract_market_name"),
            cftc_contract_market_code=latest.get("cftc_contract_market_code"),
            as_of=_parse_date(latest.get(_DATE_FIELD)),
            open_interest=open_interest,
            noncomm_long=noncomm_long,
            noncomm_short=noncomm_short,
            noncomm_net=noncomm_net,
            comm_long=comm_long,
            comm_short=comm_short,
            comm_net=comm_net,
            noncomm_net_pct_oi=_quantize(pct_oi, 4),
            noncomm_net_change=net_change,
            noncomm_net_zscore=_quantize(zscore, 4),
            traders_noncomm_long=_int(latest.get("traders_noncomm_long_all")),
            traders_noncomm_short=_int(latest.get("traders_noncomm_short_all")),
            history=history,
            matched_markets=others,
            note=note,
        )


def _week(row: dict) -> CotWeek | None:
    report_date = _parse_date(row.get(_DATE_FIELD))
    if report_date is None:
        return None
    noncomm_long = _dec(row.get("noncomm_positions_long_all"))
    noncomm_short = _dec(row.get("noncomm_positions_short_all"))
    return CotWeek(
        report_date=report_date,
        noncomm_long=noncomm_long,
        noncomm_short=noncomm_short,
        noncomm_net=_diff(noncomm_long, noncomm_short),
        open_interest=_dec(row.get("open_interest_all")),
    )
