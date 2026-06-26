"""Technical indicators — pure, source-agnostic math over a price series.

Kept separate from any adapter so the formulas are unit-testable in isolation and reusable on
any ``PriceHistory`` (yfinance today, anything tomorrow). Output is raw numbers: no "uptrend"
or "overbought" verdict — the agent reads RSI/price-vs-SMA and concludes (see DECISIONS ADR-004).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from .domain.models import PriceHistory, Technicals

_WEEK52_BARS = 252  # ~ one trading year


def sma(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def ema_series(values: list[float], window: int) -> list[float]:
    """EMA aligned so index 0 corresponds to input index ``window-1`` (seeded with the SMA)."""
    if len(values) < window:
        return []
    k = 2 / (window + 1)
    current = sum(values[:window]) / window
    out = [current]
    for value in values[window:]:
        current = value * k + current * (1 - k)
        out.append(current)
    return out


def ema_last(values: list[float], window: int) -> float | None:
    series = ema_series(values, window)
    return series[-1] if series else None


def rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def macd(
    values: list[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[float | None, float | None, float | None]:
    if len(values) < slow + signal:
        return None, None, None
    ema_fast = ema_series(values, fast)
    ema_slow = ema_series(values, slow)
    offset = slow - fast  # align the longer fast-EMA onto the slow-EMA timeline
    macd_line = [f - s for f, s in zip(ema_fast[offset:], ema_slow, strict=False)]
    signal_series = ema_series(macd_line, signal)
    if not signal_series:
        return macd_line[-1], None, None
    macd_value = macd_line[-1]
    signal_value = signal_series[-1]
    return macd_value, signal_value, macd_value - signal_value


def atr(
    highs: list[float], lows: list[float], closes: list[float], period: int = 14
) -> float | None:
    n = len(closes)
    if n < period + 1 or len(highs) != n or len(lows) != n:
        return None
    true_ranges = []
    for i in range(1, n):
        true_ranges.append(
            max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        )
    current = sum(true_ranges[:period]) / period
    for i in range(period, len(true_ranges)):
        current = (current * (period - 1) + true_ranges[i]) / period
    return current


def _q(value: float | None, places: int) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)


def compute_technicals(history: PriceHistory) -> Technicals:
    """Compute the indicator set from a ``PriceHistory`` (expects daily bars, oldest→newest)."""
    closes = [float(b.close) for b in history.bars if b.close is not None]
    highs = [float(b.high) for b in history.bars if b.high is not None]
    lows = [float(b.low) for b in history.bars if b.low is not None]

    macd_value, signal_value, histogram = macd(closes)
    recent = history.bars[-_WEEK52_BARS:]
    high52 = max((float(b.high) for b in recent if b.high is not None), default=None)
    low52 = min((float(b.low) for b in recent if b.low is not None), default=None)

    return Technicals(
        symbol=history.symbol,
        as_of=history.as_of,
        last_price=_q(closes[-1] if closes else None, 4),
        sma_50=_q(sma(closes, 50), 4),
        sma_200=_q(sma(closes, 200), 4),
        ema_20=_q(ema_last(closes, 20), 4),
        rsi_14=_q(rsi(closes, 14), 2),
        macd=_q(macd_value, 4),
        macd_signal=_q(signal_value, 4),
        macd_histogram=_q(histogram, 4),
        atr_14=_q(atr(highs, lows, closes, 14), 4),
        week52_high=_q(high52, 4),
        week52_low=_q(low52, 4),
        bars_used=len(closes),
    )
