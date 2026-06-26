from datetime import date, timedelta
from decimal import Decimal

from scout.analytics import (
    atr,
    compute_technicals,
    ema_last,
    macd,
    pct_returns,
    pearson,
    rsi,
    sma,
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
    assert tech.bars_used == 10
