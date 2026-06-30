import random
from datetime import date, timedelta
from decimal import Decimal

from scout.adapters.statarb import CointegrationAnalyzer
from scout.analytics import (
    dickey_fuller_tstat,
    mean_reversion_half_life,
    ols_with_intercept,
)
from scout.domain.models import PriceBar, PriceHistory

# --- pure analytics (deterministic) ---------------------------------------------


def test_ols_with_intercept_recovers_slope_and_intercept():
    # y = 2x + 1 exactly.
    slope, intercept = ols_with_intercept([3, 5, 7, 9], [1, 2, 3, 4])
    assert round(slope, 6) == 2.0
    assert round(intercept, 6) == 1.0


def test_ols_returns_none_on_zero_variance_regressor():
    assert ols_with_intercept([1, 2, 3], [5, 5, 5]) is None


def test_dickey_fuller_strongly_negative_on_mean_reverting_series():
    # A stationary AR(1) with phi=0.5 mean-reverts hard → DF t-stat well below the 5% level.
    random.seed(3)
    series = [0.0]
    for _ in range(200):
        series.append(0.5 * series[-1] + random.gauss(0, 1))
    stat = dickey_fuller_tstat(series)
    assert stat is not None and stat < -3.34


def test_half_life_none_on_non_reverting_trend():
    # A monotone series doesn't revert (gamma >= 0) → no meaningful half-life.
    assert mean_reversion_half_life([float(i) for i in range(50)]) is None


def test_half_life_positive_on_mean_reverting_series():
    random.seed(4)
    series = [0.0]
    for _ in range(200):
        series.append(0.5 * series[-1] + random.gauss(0, 1))
    hl = mean_reversion_half_life(series)
    assert hl is not None and hl > 0


# --- adapter ---------------------------------------------------------------------


def _history(symbol, closes):
    start = date(2024, 1, 1)
    bars = [
        PriceBar(date=start + timedelta(days=i), close=Decimal(str(round(close, 6))))
        for i, close in enumerate(closes)
    ]
    return PriceHistory(symbol=symbol, interval="1d", bars=bars, as_of=bars[-1].date)


def _analyzer(series):
    async def _fetch(symbol):
        closes = series.get(symbol)
        return None if closes is None else _history(symbol, closes)

    return CointegrationAnalyzer(_fetch)


async def test_cointegrated_pair_detected():
    # B is a random walk; A = 2*B + 10 + a stationary AR(1) residual → A,B cointegrated, beta≈2.
    random.seed(1)
    n = 200
    b, resid = [100.0], [0.0]
    for _ in range(n - 1):
        b.append(b[-1] + random.gauss(0, 1))
        resid.append(0.5 * resid[-1] + random.gauss(0, 1))
    a = [2 * b[i] + 10 + resid[i] for i in range(n)]

    result = await _analyzer({"A": a, "B": b}).get_cointegration("A", "B", lookback_days=200)
    assert result.n_obs == 200
    assert result.is_cointegrated is True
    assert result.adf_stat is not None and float(result.adf_stat) < -3.34
    assert abs(float(result.hedge_ratio_beta) - 2.0) < 0.1
    assert result.half_life_days is not None and float(result.half_life_days) > 0
    assert result.spread_zscore is not None
    assert result.source_status is None


async def test_independent_random_walks_not_cointegrated():
    # Two independent random walks → the residual spread has a unit root → not cointegrated.
    random.seed(11)
    n = 200
    a, b = [50.0], [50.0]
    for _ in range(n - 1):
        a.append(a[-1] + random.gauss(0, 1))
        b.append(b[-1] + random.gauss(0, 1))
    result = await _analyzer({"A": a, "B": b}).get_cointegration("A", "B", lookback_days=200)
    assert result.is_cointegrated is False
    assert result.adf_stat is not None and float(result.adf_stat) > -3.34


async def test_short_overlap_nulls_stats_with_note():
    result = await _analyzer({"A": [1, 2, 3, 4, 5], "B": [2, 4, 6, 8, 10]}).get_cointegration(
        "A", "B"
    )
    assert result.n_obs == 5
    assert result.adf_stat is None
    assert result.is_cointegrated is None
    assert result.note is not None and "Insufficient" in result.note


async def test_leg_fetch_failure_sets_source_status():
    async def _fetch(symbol):
        if symbol == "B":
            raise TimeoutError("boom")
        return _history(symbol, [float(i) for i in range(60)])

    result = await CointegrationAnalyzer(_fetch).get_cointegration("A", "B")
    assert result.source_status is not None and "symbol_b" in result.source_status
    assert result.is_cointegrated is None


async def test_crit_values_always_present():
    result = await _analyzer({"A": [1, 2], "B": [1, 2]}).get_cointegration("A", "B")
    assert result.adf_crit_5pct == Decimal("-3.34")
    assert result.adf_crit_1pct == Decimal("-3.90")
    assert result.adf_crit_10pct == Decimal("-3.04")
