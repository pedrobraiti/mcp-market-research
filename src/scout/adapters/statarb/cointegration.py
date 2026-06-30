"""Engle-Granger cointegration / pairs analyzer — pure stats over Scout's existing price path.

Adds NO new HTTP client and NO heavy dependency (no scipy/statsmodels): it takes an injected
``fetch_history(symbol) -> PriceHistory | None`` (the yfinance ``MarketDataSource`` in the
composition root) and runs the Engle-Granger two-step in pure Python (``scout.analytics``).

Step 1 — OLS hedge ratio (regress A on B). Step 2 — a Dickey-Fuller test on the residual spread.
We report the DF t-statistic against MacKinnon's asymptotic Engle-Granger critical values rather
than a fake-precise p-value (honesty over filling, ADR-004/ADR-012). The two close series are
aligned by their date intersection and sliced to the requested ``lookback_days`` so a stale or
missing day in one leg never silently mismatches the other.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from ...analytics import (
    EG_CRITICAL_VALUES,
    dickey_fuller_tstat,
    mean_reversion_half_life,
    ols_with_intercept,
    zscore_of_last,
)
from ...domain.models import Cointegration, PriceHistory
from ..retry import unavailable_status

_MIN_OBS = 30  # below this the pair test is too short to mean anything
_DEFAULT_LOOKBACK = 252
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


class CointegrationAnalyzer:
    def __init__(self, fetch_history: FetchHistory) -> None:
        self._fetch_history = fetch_history

    async def _leg(self, symbol: str) -> tuple[dict[date, float], str | None]:
        try:
            history = await self._fetch_history(symbol)
        except Exception as exc:  # noqa: BLE001 — a fetch error is honest unavailability, not data
            return {}, unavailable_status(exc)
        return _closes_by_date(history), None

    async def get_cointegration(
        self, symbol_a: str, symbol_b: str, lookback_days: int = _DEFAULT_LOOKBACK
    ) -> Cointegration:
        lookback = max(_MIN_OBS, lookback_days)
        closes_a, status_a = await self._leg(symbol_a)
        closes_b, status_b = await self._leg(symbol_b)

        statuses = [
            f"{label} {status}"
            for label, status in (("symbol_a", status_a), ("symbol_b", status_b))
            if status
        ]
        source_status = "; ".join(statuses) if statuses else None

        common = sorted(set(closes_a) & set(closes_b))[-lookback:]
        result = Cointegration(
            symbol_a=symbol_a.upper(),
            symbol_b=symbol_b.upper(),
            lookback_days=lookback_days,
            n_obs=len(common),
            adf_crit_1pct=_quantize(EG_CRITICAL_VALUES["1pct"], 2),
            adf_crit_5pct=_quantize(EG_CRITICAL_VALUES["5pct"], 2),
            adf_crit_10pct=_quantize(EG_CRITICAL_VALUES["10pct"], 2),
            as_of=common[-1] if common else None,
            source_status=source_status,
        )

        if len(common) < _MIN_OBS:
            result.note = (
                f"Insufficient overlapping daily closes ({len(common)} < {_MIN_OBS}) to test the "
                "pair — widen the lookback or check the symbols."
            )
            return result

        series_a = [closes_a[day] for day in common]
        series_b = [closes_b[day] for day in common]
        fit = ols_with_intercept(series_a, series_b)
        if fit is None:
            result.note = "Degenerate hedge-ratio fit (symbol_b has no variance over the window)."
            return result

        beta, intercept = fit
        spread = [series_a[i] - (intercept + beta * series_b[i]) for i in range(len(common))]
        adf = dickey_fuller_tstat(spread)
        half_life = mean_reversion_half_life(spread)
        z = zscore_of_last(spread)

        result.hedge_ratio_beta = _quantize(beta, 6)
        result.spread_latest = _quantize(spread[-1], 6)
        result.spread_zscore = _quantize(z, 4)
        result.adf_stat = _quantize(adf, 4)
        result.is_cointegrated = adf is not None and adf < EG_CRITICAL_VALUES["5pct"]
        result.half_life_days = _quantize(half_life, 2)
        result.note = (
            "Engle-Granger two-step: OLS hedge ratio then a non-augmented (0-lag) Dickey-Fuller "
            "test on the residual; adf_stat is judged against MacKinnon asymptotic critical values "
            "(constant, no trend, one regressor). Uses yfinance split/div-adjusted closes."
        )
        return result
