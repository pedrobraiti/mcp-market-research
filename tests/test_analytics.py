from datetime import date, timedelta
from decimal import Decimal

from scout.analytics import (
    atr,
    calmar_ratio,
    compute_technicals,
    ema_last,
    excess_kurtosis,
    log_returns,
    macd,
    max_drawdown,
    max_drawdown_duration,
    momentum,
    momentum_12_1,
    pct_returns,
    pearson,
    realized_volatility,
    rogers_satchell_volatility,
    rsi,
    sharpe_ratio,
    skewness,
    sma,
    sortino_ratio,
    yang_zhang_volatility,
)
from scout.domain.models import PriceBar, PriceHistory


def test_sma_exact():
    assert sma([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5) == 8.0
    assert sma([1, 2, 3], 5) is None


def test_rsi_extremes():
    rising = list(range(1, 30))
    falling = list(range(30, 1, -1))
    assert rsi(rising, 14) == 100.0  # only gains
    assert rsi(falling, 14) == 0.0  # only losses
    assert rsi([1, 2, 3], 14) is None  # not enough data


def test_ema_last_tracks_recent_values():
    value = ema_last([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5)
    assert value is not None
    assert 7.0 < value < 10.0  # weighted toward the recent higher values


def test_macd_needs_enough_data():
    assert macd([1, 2, 3]) == (None, None, None)
    line, signal, hist = macd(list(range(1, 60)))
    assert line is not None and signal is not None and hist is not None


def test_atr_constant_range():
    highs = [i + 1 for i in range(1, 30)]
    lows = [i - 1 for i in range(1, 30)]
    closes = list(range(1, 30))
    assert atr(highs, lows, closes, 14) == 2.0
    assert atr([1], [1], [1], 14) is None


def test_pct_returns():
    result = pct_returns([10.0, 11.0, 12.0])
    assert abs(result[0] - 0.1) < 1e-9
    assert abs(result[1] - 0.090909) < 1e-5


def test_pearson_correlation():
    assert pearson([1, 2, 3], [2, 4, 6]) == 1.0  # perfectly positively correlated
    assert pearson([1, 2, 3], [6, 4, 2]) == -1.0  # perfectly negatively correlated
    assert pearson([1, 2, 3], [1, 1, 1]) is None  # zero variance → undefined
    assert pearson([1, 2], [1]) is None  # mismatched lengths


def test_log_returns_skips_nonpositive():
    rets = log_returns([10.0, 11.0, 0.0, 12.0])
    assert len(rets) == 1  # only the 10→11 step is valid (0 breaks ln on both sides)
    assert abs(rets[0] - 0.0953) < 1e-3


def test_realized_volatility_minimum_and_positivity():
    assert realized_volatility([1.0, 2.0, 3.0]) is None  # not enough returns
    closes = [100.0 * (1.01 ** i if i % 2 == 0 else 1.005 ** i) for i in range(60)]
    vol = realized_volatility(closes, periods_per_year=252)
    assert vol is not None and vol > 0


def test_ohlc_volatility_estimators_positive_on_ramp():
    opens = [float(i) for i in range(1, 40)]
    highs = [i + 1.0 for i in range(1, 40)]
    lows = [i - 1.0 for i in range(1, 40)]
    closes = [float(i) for i in range(1, 40)]
    rs = rogers_satchell_volatility(opens, highs, lows, closes)
    yz = yang_zhang_volatility(opens, highs, lows, closes)
    assert rs is not None and rs > 0
    assert yz is not None and yz > 0
    assert rogers_satchell_volatility([1.0], [1.0], [1.0], [1.0]) is None  # too short


def test_sharpe_and_sortino_need_sample_and_reward_consistency():
    assert sharpe_ratio([0.01, 0.01]) is None  # below minimum sample
    steady = [0.01, -0.002] * 30  # positive drift, modest noise
    volatile = [0.05, -0.045] * 30  # same-ish drift, far more noise
    s_steady = sharpe_ratio(steady)
    s_volatile = sharpe_ratio(volatile)
    assert s_steady is not None and s_volatile is not None
    assert s_steady > s_volatile  # less noise → higher Sharpe
    assert sortino_ratio(steady) is not None


def test_max_drawdown_and_duration():
    closes = [100.0, 120.0, 90.0, 130.0]
    assert abs(max_drawdown(closes) - (-0.25)) < 1e-9  # 120 → 90 is the worst
    assert max_drawdown_duration(closes) == 1  # one bar spent below the prior peak
    assert max_drawdown([100.0, 110.0, 120.0]) == 0.0  # monotonic up → no drawdown


def test_calmar_ratio_rewards_return_over_pain():
    rising = [100.0 + i for i in range(40)]  # steady climb, tiny drawdowns
    calmar = calmar_ratio(rising, periods_per_year=252)
    assert calmar is None or calmar > 0  # no real drawdown may yield None or a positive ratio


def test_skewness_symmetric_is_near_zero():
    symmetric = [-2.0, -1.0, 0.0, 1.0, 2.0] * 12  # 60 points, symmetric
    skew = skewness(symmetric)
    assert skew is not None and abs(skew) < 1e-6
    assert excess_kurtosis(symmetric) is not None
    assert skewness([1.0, 2.0, 3.0]) is None  # below minimum sample


def test_momentum_horizons():
    closes = [float(i) for i in range(1, 11)]  # 1..10
    assert abs(momentum(closes, 2) - (10.0 / 8.0 - 1)) < 1e-9
    assert momentum(closes, 20) is None  # lookback exceeds series
    assert momentum_12_1([1.0, 2.0, 3.0]) is None  # needs > 252 bars


def _ramp_history(n: int) -> PriceHistory:
    base = date(2024, 1, 1)
    bars = [
        PriceBar(
            date=base + timedelta(days=i),
            open=Decimal(i),
            high=Decimal(i + 1),
            low=Decimal(i - 1),
            close=Decimal(i),
            volume=1000,
        )
        for i in range(1, n + 1)
    ]
    return PriceHistory(symbol="TEST", interval="1d", bars=bars, as_of=None)


def test_compute_technicals_on_ramp():
    tech = compute_technicals(_ramp_history(250))
    assert tech.last_price == Decimal("250")
    assert tech.sma_50 == Decimal("225.5")
    assert tech.sma_200 == Decimal("150.5")
    assert tech.rsi_14 == Decimal("100")
    assert tech.atr_14 == Decimal("2")
    assert tech.week52_high == Decimal("251")
    assert tech.week52_low == Decimal("0")
    assert tech.bars_used == 250
    assert tech.macd is not None


def test_compute_technicals_short_series_partial():
    tech = compute_technicals(_ramp_history(10))
    assert tech.last_price == Decimal("10")
    assert tech.sma_50 is None  # not enough bars
    assert tech.volatility_annualized is None  # below the vol minimum too
    assert tech.bars_used == 10


def test_compute_technicals_populates_derived_layer():
    tech = compute_technicals(_ramp_history(260))
    assert tech.volatility_annualized is not None
    assert tech.volatility_ohlc is not None
    assert tech.volatility_estimator == "yang_zhang"  # equities default → gaps modeled
    assert tech.atr_pct is not None and tech.atr_pct > 0
    assert tech.range_position_52w is not None
    assert tech.sharpe_ratio is not None
    assert tech.momentum_12m is not None
    assert tech.momentum_12_1 is not None
    assert tech.max_drawdown is not None
    assert tech.annualization_factor == 252


def test_compute_technicals_crypto_calibration():
    tech = compute_technicals(_ramp_history(260), periods_per_year=365, overnight_gaps=False)
    assert tech.annualization_factor == 365
    assert tech.volatility_estimator == "rogers_satchell"  # no overnight gap in 24/7 markets
