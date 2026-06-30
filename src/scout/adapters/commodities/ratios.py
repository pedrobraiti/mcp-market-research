"""Commodity bellwether ratios — copper/gold and gold/silver.

Closes the copper-gold ratio deferred from the macro wave. This adds NO new HTTP client: it
REUSES Scout's existing price path (the yfinance ``MarketDataSource``) by taking an injected
``fetch_history(symbol) -> PriceHistory | None`` callable. That keeps offline tests fully synthetic
(inject a tiny ``PriceHistory``) and means the futures quotes come through the one price adapter
already in the composition root.

Tickers: ``HG=F`` (copper, $/lb), ``GC=F`` (gold, $/oz), ``SI=F`` (silver, $/oz). For each ratio
the three close series are aligned by date (intersection per pair) before dividing, so a stale or
missing day in one leg never silently mismatches the other. The ratio LEVEL is arbitrary — the
latest value plus its z-score over ~1y of daily ratios is the read (a measure, not a verdict;
ADR-004). A missing leg leaves that ratio null with a ``note``; a fetch failure on a leg sets
``source_status`` (ADR-012).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from ...analytics import zscore_of_last
from ...domain.models import CommodityRatios, PriceHistory, RatioPoint
from ..retry import unavailable_status

_COPPER = "HG=F"
_GOLD = "GC=F"
_SILVER = "SI=F"
_MIN_POINTS_FOR_ZSCORE = 30  # below this a z-score over the daily ratio series is too noisy
_RANGE = "1y"

FetchHistory = Callable[[str], Awaitable[PriceHistory | None]]


def _quantize(value: float | None, places: int) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)


def _closes_by_date(history: PriceHistory | None) -> dict[date, float]:
    if history is None:
        return {}
    out: dict[date, float] = {}
    for bar in history.bars:
        if bar.close is not None:
            close = float(bar.close)
            if close > 0:
                out[bar.date] = close
    return out


def _latest_close(closes: dict[date, float]) -> float | None:
    if not closes:
        return None
    return closes[max(closes)]


def _aligned_ratio(
    numerator: dict[date, float], denominator: dict[date, float]
) -> list[tuple[date, float]]:
    """Daily ratio over the date intersection of two close series, oldest → newest."""
    common = sorted(set(numerator) & set(denominator))
    return [(day, numerator[day] / denominator[day]) for day in common if denominator[day] != 0]


class CommodityRatioCalculator:
    def __init__(self, fetch_history: FetchHistory, range_: str = _RANGE) -> None:
        self._fetch_history = fetch_history
        self._range = range_

    async def _leg(self, symbol: str) -> tuple[dict[date, float], str | None]:
        try:
            history = await self._fetch_history(symbol)
        except Exception as exc:  # noqa: BLE001 — a fetch error is honest unavailability, not data
            return {}, unavailable_status(exc)
        return _closes_by_date(history), None

    async def get_ratios(self) -> CommodityRatios:
        copper, copper_status = await self._leg(_COPPER)
        gold, gold_status = await self._leg(_GOLD)
        silver, silver_status = await self._leg(_SILVER)

        statuses = [
            f"{label} {status}"
            for label, status in (
                ("copper", copper_status),
                ("gold", gold_status),
                ("silver", silver_status),
            )
            if status
        ]
        source_status = "; ".join(statuses) if statuses else None

        copper_gold_series = _aligned_ratio(copper, gold)
        gold_silver_series = _aligned_ratio(gold, silver)

        copper_gold_value = copper_gold_series[-1][1] if copper_gold_series else None
        gold_silver_value = gold_silver_series[-1][1] if gold_silver_series else None

        cg_values = [ratio for _, ratio in copper_gold_series]
        gs_values = [ratio for _, ratio in gold_silver_series]
        copper_gold_z = (
            zscore_of_last(cg_values) if len(cg_values) >= _MIN_POINTS_FOR_ZSCORE else None
        )
        gold_silver_z = (
            zscore_of_last(gs_values) if len(gs_values) >= _MIN_POINTS_FOR_ZSCORE else None
        )

        cg_by_date = dict(copper_gold_series)
        gs_by_date = dict(gold_silver_series)
        history = [
            RatioPoint(
                date=day,
                copper_gold=_quantize(cg_by_date.get(day), 6),
                gold_silver=_quantize(gs_by_date.get(day), 4),
            )
            for day in sorted(set(cg_by_date) | set(gs_by_date))
        ]
        as_of = history[-1].date if history else None

        notes: list[str] = []
        if copper_gold_value is None:
            missing = "copper" if not copper else "gold"
            notes.append(f"copper/gold unavailable (no aligned data for the {missing} leg)")
        if gold_silver_value is None:
            missing = "gold" if not gold else "silver"
            notes.append(f"gold/silver unavailable (no aligned data for the {missing} leg)")
        note = "; ".join(notes) if notes else None

        return CommodityRatios(
            copper_gold=_quantize(copper_gold_value, 6),
            copper_gold_zscore=_quantize(copper_gold_z, 4),
            gold_silver=_quantize(gold_silver_value, 4),
            gold_silver_zscore=_quantize(gold_silver_z, 4),
            copper_price=_quantize(_latest_close(copper), 4),
            gold_price=_quantize(_latest_close(gold), 4),
            silver_price=_quantize(_latest_close(silver), 4),
            history=history,
            as_of=as_of,
            source_status=source_status,
            note=note,
        )
