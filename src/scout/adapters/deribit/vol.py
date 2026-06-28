"""Deribit DVOL — the 'crypto VIX' (options-implied volatility index), keyless.

Deribit's public JSON-RPC-over-HTTP endpoints need no key. Two reads: the current DVOL index value
and its recent daily OHLC history, for BTC or ETH. Raw index — how much swing the options market
prices — useful to size a stop or read the vol regime; not a trade call.

The JSON fetch is injected so the unit tests run fully offline.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from ...analytics import percentile_of_last, zscore_of_last
from ...domain.models import CryptoImpliedVol, VolPoint

_BASE = "https://www.deribit.com/api/v2/public"
_DAY_MS = 86_400_000
_HISTORY_DAYS = 180  # ~6 months of daily DVOL for a meaningful vol-regime z-score/percentile
_MIN_FOR_REGIME = 20  # below this the z-score/percentile is too noisy to report


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _ms_to_dt(ms: Any) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=UTC)
    except (TypeError, ValueError, OverflowError):
        return None


def _round(value: float | None, places: int) -> Decimal | None:
    return None if value is None else Decimal(str(round(value, places)))


class DeribitVol:
    def __init__(
        self,
        fetch_json: Callable[[str], Awaitable[Any]] | None = None,
        timeout: float = 15.0,
        now_ms: int | None = None,
    ) -> None:
        self._timeout = timeout
        self._fetch_json = fetch_json or self._default_fetch_json
        self._now_ms = now_ms

    async def _default_fetch_json(self, url: str) -> Any:
        import httpx

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    def _window(self, days: int) -> tuple[int, int]:
        end = self._now_ms or int(datetime.now(tz=UTC).timestamp() * 1000)
        return end - days * _DAY_MS, end

    async def get_implied_vol(self, asset: str = "BTC") -> CryptoImpliedVol:
        currency = asset.strip().upper()
        if currency not in ("BTC", "ETH"):
            return CryptoImpliedVol(
                asset=currency, note="Deribit DVOL is available for BTC and ETH only."
            )
        index_name = f"{currency.lower()}dvol_usdc"
        start, end = self._window(_HISTORY_DAYS)
        index, series = await asyncio.gather(
            self._fetch_json(f"{_BASE}/get_index_price?index_name={index_name}"),
            self._fetch_json(
                f"{_BASE}/get_volatility_index_data?currency={currency}"
                f"&start_timestamp={start}&end_timestamp={end}&resolution=1D"
            ),
            return_exceptions=True,
        )
        current = None
        if isinstance(index, dict):
            current = _dec((index.get("result") or {}).get("index_price"))
        history: list[VolPoint] = []
        if isinstance(series, dict):
            for row in (series.get("result") or {}).get("data") or []:
                if not row or len(row) < 5:
                    continue
                stamp = _ms_to_dt(row[0])
                if stamp is None:
                    continue
                history.append(
                    VolPoint(
                        timestamp=stamp,
                        open=_dec(row[1]),
                        high=_dec(row[2]),
                        low=_dec(row[3]),
                        close=_dec(row[4]),
                    )
                )
        z = pct = None
        closes = [float(p.close) for p in history if p.close is not None]
        if current is not None and len(closes) >= _MIN_FOR_REGIME:
            window = [*closes, float(current)]  # score the current DVOL within its own history
            z = zscore_of_last(window)
            scored = percentile_of_last(window)
            pct = scored * 100 if scored is not None else None
        return CryptoImpliedVol(
            asset=currency,
            dvol_current=current,
            dvol_zscore=_round(z, 2),
            dvol_percentile=_round(pct, 1),
            history=history,
        )
