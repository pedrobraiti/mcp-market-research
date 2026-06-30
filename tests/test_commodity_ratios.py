from datetime import date, timedelta
from decimal import Decimal

from scout.adapters.commodities import CommodityRatioCalculator
from scout.domain.models import PriceBar, PriceHistory

_COPPER = "HG=F"
_GOLD = "GC=F"
_SILVER = "SI=F"


def _history(symbol, closes):
    start = date(2025, 1, 1)
    bars = [
        PriceBar(date=start + timedelta(days=i), close=Decimal(str(close)))
        for i, close in enumerate(closes)
    ]
    return PriceHistory(symbol=symbol, interval="1d", bars=bars, as_of=bars[-1].date)


def _calculator(series):
    """`series` maps symbol → list of closes (or None to simulate a missing leg)."""

    async def _fetch(symbol):
        closes = series.get(symbol)
        return None if closes is None else _history(symbol, closes)

    return CommodityRatioCalculator(_fetch)


async def test_ratios_and_zscore_null_under_min_points():
    # 5 aligned days, constant closes: copper=4, gold=2000, silver=25.
    calc = _calculator({_COPPER: [4] * 5, _GOLD: [2000] * 5, _SILVER: [25] * 5})
    result = await calc.get_ratios()
    assert result.copper_gold == Decimal("0.002")  # 4 / 2000
    assert result.gold_silver == Decimal("80")  # 2000 / 25
    assert result.copper_price == Decimal("4")
    assert result.gold_price == Decimal("2000")
    assert result.silver_price == Decimal("25")
    # < 30 aligned points → z-score too noisy to report.
    assert result.copper_gold_zscore is None
    assert result.gold_silver_zscore is None
    assert result.source_status is None
    assert result.note is None
    assert len(result.history) == 5


async def test_zscore_present_with_enough_points():
    # 40 aligned days; copper varies so the copper/gold ratio has non-zero variance.
    copper = [4 + (i % 3) * 0.1 for i in range(40)]
    calc = _calculator({_COPPER: copper, _GOLD: [2000] * 40, _SILVER: [25] * 40})
    result = await calc.get_ratios()
    assert result.copper_gold_zscore is not None
    # gold and silver are both flat → zero variance → still null even with enough points.
    assert result.gold_silver_zscore is None


async def test_missing_silver_leg_nulls_gold_silver_with_note():
    calc = _calculator({_COPPER: [4] * 5, _GOLD: [2000] * 5, _SILVER: None})
    result = await calc.get_ratios()
    assert result.copper_gold == Decimal("0.002")  # copper/gold still computed
    assert result.gold_silver is None
    assert result.silver_price is None
    assert result.note is not None and "gold/silver" in result.note
