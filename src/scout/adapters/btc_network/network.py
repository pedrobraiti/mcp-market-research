"""BTC base-layer fundamentals + fee market — keyless, two sources composed.

Source A — Blockchain.com Charts (``api.blockchain.info/charts/{chart}``): hash rate, miner
revenue, on-chain tx count, on-chain settlement USD volume and market cap. NVT is NOT a chart — it
is COMPUTED here as ``market_cap / estimated_transaction_volume_usd`` (the REAL NVT: on-chain
settlement volume, not exchange volume), plus a 90-day-smoothed ``nvt_90d`` (classic NVT smooths the
denominator).

Source B — mempool.space (``/api/v1/fees/recommended`` and ``/api/v1/difficulty-adjustment``): the
live sat/vB fee tiers and the current difficulty retarget.

The two legs fail independently: if one source is throttled the other still returns, with the gap
recorded in ``partial``/``note`` and a missing field left null (never a faked number — ADR-012).

The JSON fetch is injected so the unit tests run fully offline.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from ...domain.models import BtcNetwork, BtcNetworkPoint
from ..retry import unavailable_status, with_retry

_CHART_URL = "https://api.blockchain.info/charts/{chart}?timespan={weeks}weeks&format=json"
_MEMPOOL = "https://mempool.space/api"
# 26 weeks (~182 daily points) so the 90-day NVT average has enough samples to compute.
_CHART_WEEKS = 26
_MIN_POINTS_FOR_NVT_90D = 90
_HISTORY_POINTS = 14  # tail of the headline series (hash rate + NVT) returned for context
# Blockchain.com chart names (verified): note the PLURAL "miners-revenue".
_HASH_RATE = "hash-rate"
_MINERS_REVENUE = "miners-revenue"
_N_TRANSACTIONS = "n-transactions"
_TX_VOLUME = "estimated-transaction-volume-usd"  # on-chain settlement USD volume
_MARKET_CAP = "market-cap"
_CHARTS = [_HASH_RATE, _MINERS_REVENUE, _N_TRANSACTIONS, _TX_VOLUME, _MARKET_CAP]


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return None if result.is_nan() else result


def _series(chart: Any) -> list[tuple[int, Decimal]]:
    """Extract the ``[(unix_ts, value), …]`` series from a Blockchain.com chart payload."""
    if not isinstance(chart, dict):
        return []
    out: list[tuple[int, Decimal]] = []
    for point in chart.get("values") or []:
        if not isinstance(point, dict):
            continue
        ts = point.get("x")
        value = _dec(point.get("y"))
        if ts is not None and value is not None:
            try:
                out.append((int(ts), value))
            except (TypeError, ValueError):
                continue
    return out


def _latest(series: list[tuple[int, Decimal]]) -> Decimal | None:
    return series[-1][1] if series else None


def _epoch_ms_to_dt(value: Any) -> datetime | None:
    ms = _dec(value)
    if ms is None:
        return None
    try:
        return datetime.fromtimestamp(float(ms) / 1000, tz=UTC)
    except (OverflowError, OSError, ValueError):
        return None


class BtcNetworkData:
    def __init__(
        self,
        fetch_json: Callable[[str], Awaitable[Any]] | None = None,
        timeout: float = 20.0,
        retry_attempts: int = 3,
        retry_base_delay: float = 0.5,
    ) -> None:
        self._timeout = timeout
        self._retry_attempts = retry_attempts
        self._retry_base_delay = retry_base_delay
        self._fetch_json = fetch_json or self._default_fetch_json

    async def _default_fetch_json(self, url: str) -> Any:
        import httpx

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def _fetch_retry(self, url: str) -> Any:
        return await with_retry(
            lambda: self._fetch_json(url),
            attempts=self._retry_attempts,
            base_delay=self._retry_base_delay,
        )

    async def get_network(self) -> BtcNetwork:
        chart_coros = [
            self._fetch_retry(_CHART_URL.format(chart=chart, weeks=_CHART_WEEKS))
            for chart in _CHARTS
        ]
        fees_coro = self._fetch_retry(f"{_MEMPOOL}/v1/fees/recommended")
        diff_coro = self._fetch_retry(f"{_MEMPOOL}/v1/difficulty-adjustment")
        results = await asyncio.gather(
            *chart_coros, fees_coro, diff_coro, return_exceptions=True
        )
        chart_results = results[: len(_CHARTS)]
        fees_result, diff_result = results[len(_CHARTS)], results[len(_CHARTS) + 1]

        model = BtcNetwork()
        self._apply_fundamentals(model, chart_results)
        self._apply_fee_market(model, fees_result, diff_result)
        self._apply_status(model, chart_results, fees_result, diff_result)
        return model

    def _apply_fundamentals(
        self, model: BtcNetwork, chart_results: list[Any]
    ) -> None:
        series = {
            chart: _series(result) if not isinstance(result, Exception) else []
            for chart, result in zip(_CHARTS, chart_results, strict=True)
        }
        model.hash_rate = _latest(series[_HASH_RATE])
        model.miners_revenue_usd = _latest(series[_MINERS_REVENUE])
        model.n_transactions = _latest(series[_N_TRANSACTIONS])
        model.tx_volume_usd = _latest(series[_TX_VOLUME])
        model.market_cap_usd = _latest(series[_MARKET_CAP])

        if model.market_cap_usd is not None and model.tx_volume_usd:
            model.nvt = model.market_cap_usd / model.tx_volume_usd

        tx_values = [value for _, value in series[_TX_VOLUME]]
        if model.market_cap_usd is not None and len(tx_values) >= _MIN_POINTS_FOR_NVT_90D:
            window = tx_values[-_MIN_POINTS_FOR_NVT_90D:]
            avg = sum(window) / Decimal(len(window))
            if avg > 0:
                model.nvt_90d = model.market_cap_usd / avg

        model.history = self._build_history(series, model.market_cap_usd)
        if series[_MARKET_CAP]:
            model.as_of = datetime.fromtimestamp(series[_MARKET_CAP][-1][0], tz=UTC)
        elif series[_HASH_RATE]:
            model.as_of = datetime.fromtimestamp(series[_HASH_RATE][-1][0], tz=UTC)

    @staticmethod
    def _by_date(points: list[tuple[int, Decimal]]) -> dict[Any, Decimal]:
        """Map a (unix_ts, value) series to {date: value}. The Blockchain.com charts don't share a
        timestamp grid — hash-rate/tx-volume are midnight-aligned but market-cap is intraday — so an
        exact-ts join drops every NVT point. A calendar-date join (last value per day) fixes it."""
        return {datetime.fromtimestamp(ts, tz=UTC).date(): value for ts, value in points}

    def _build_history(
        self, series: dict[str, list[tuple[int, Decimal]]], market_cap: Decimal | None
    ) -> list[BtcNetworkPoint]:
        mcap_by_date = self._by_date(series[_MARKET_CAP])
        txvol_by_date = self._by_date(series[_TX_VOLUME])
        points: list[BtcNetworkPoint] = []
        for ts, hash_rate in series[_HASH_RATE][-_HISTORY_POINTS:]:
            day = datetime.fromtimestamp(ts, tz=UTC).date()
            mcap = mcap_by_date.get(day)
            txvol = txvol_by_date.get(day)
            nvt = mcap / txvol if mcap is not None and txvol and txvol > 0 else None
            points.append(
                BtcNetworkPoint(
                    timestamp=datetime.fromtimestamp(ts, tz=UTC),
                    hash_rate=hash_rate,
                    nvt=nvt,
                )
            )
        return points

    def _apply_fee_market(
        self, model: BtcNetwork, fees_result: Any, diff_result: Any
    ) -> None:
        if isinstance(fees_result, dict):
            model.fee_fastest = _dec(fees_result.get("fastestFee"))
            model.fee_half_hour = _dec(fees_result.get("halfHourFee"))
            model.fee_hour = _dec(fees_result.get("hourFee"))
            model.fee_economy = _dec(fees_result.get("economyFee"))
            model.fee_minimum = _dec(fees_result.get("minimumFee"))
        if isinstance(diff_result, dict):
            model.difficulty_change_pct = _dec(diff_result.get("difficultyChange"))
            model.difficulty_progress_pct = _dec(diff_result.get("progressPercent"))
            model.estimated_retarget_date = _epoch_ms_to_dt(
                diff_result.get("estimatedRetargetDate")
            )

    def _apply_status(
        self,
        model: BtcNetwork,
        chart_results: list[Any],
        fees_result: Any,
        diff_result: Any,
    ) -> None:
        fundamentals_ok = any(not isinstance(r, Exception) for r in chart_results)
        fee_market_ok = isinstance(fees_result, dict) or isinstance(diff_result, dict)
        notes: list[str] = []
        statuses: list[str] = []

        if not fundamentals_ok:
            failure = next((r for r in chart_results if isinstance(r, Exception)), None)
            status = unavailable_status(failure) if failure is not None else "unavailable: error"
            statuses.append(status)
            notes.append(f"Blockchain.com fundamentals {status}.")
        if not (isinstance(fees_result, dict) and isinstance(diff_result, dict)):
            failure = next(
                (r for r in (fees_result, diff_result) if isinstance(r, Exception)), None
            )
            status = unavailable_status(failure) if failure is not None else "unavailable: error"
            if status not in statuses:
                statuses.append(status)
            notes.append(f"mempool.space fee market {status}.")

        if statuses:
            model.source_status = "; ".join(statuses)
        model.partial = (fundamentals_ok or fee_market_ok) and bool(notes)
        if notes:
            model.note = " ".join(notes)
