from datetime import date
from decimal import Decimal

from scout.adapters.price_fallback import PriceFallbackMarketData
from scout.adapters.stooq import StooqPrices
from scout.domain.models import PriceBar, PriceHistory

_CSV = (
    "Date,Open,High,Low,Close,Volume\n"
    "2024-05-01,180.0,182.0,179.0,181.5,50000000\n"
    "2024-06-10,190.0,192.0,189.0,191.2,40000000\n"
    "2024-06-11,191.0,193.0,190.5,192.8,42000000\n"
)


def _stooq():
    async def _fetch(url: str) -> str:
        assert "aapl.us" in url
        return _CSV

    return StooqPrices(fetch_csv=_fetch)


async def test_stooq_parses_and_filters_range():
    history = await _stooq().get_price_history(
        "aapl", range="1mo", interval="1d", as_of=date(2024, 6, 11)
    )
    assert history is not None
    assert history.interval == "1d"
    # Range "1mo" ending 2024-06-11 excludes the 2024-05-01 bar.
    assert len(history.bars) == 2
    assert history.bars[-1].close == Decimal("192.8")
    assert history.bars[-1].volume == 42000000


async def test_stooq_returns_none_for_intraday():
    assert await _stooq().get_price_history("AAPL", interval="5m") is None


class _Primary:
    def __init__(self, result=None, raises=False):
        self.result = result
        self.raises = raises
        self.fallback_marker = "primary"

    async def get_price_history(self, symbol, range="6mo", interval="1d", as_of=None):
        if self.raises:
            raise RuntimeError("yfinance down")
        return self.result


class _Fallback:
    async def get_price_history(self, symbol, range="6mo", interval="1d", as_of=None):
        bars = [PriceBar(date=date(2024, 1, 1), close=Decimal("9"))]
        return PriceHistory(symbol=symbol, interval=interval, bars=bars)


def _good_history():
    return PriceHistory(
        symbol="AAPL", interval="1d", bars=[PriceBar(date=date(2024, 1, 1), close=Decimal("100"))]
    )


async def test_fallback_uses_primary_when_it_has_data():
    wrapped = PriceFallbackMarketData(_Primary(result=_good_history()), _Fallback())
    history = await wrapped.get_price_history("AAPL")
    assert history.bars[0].close == Decimal("100")  # primary


async def test_fallback_kicks_in_when_primary_empty():
    wrapped = PriceFallbackMarketData(_Primary(result=None), _Fallback())
    history = await wrapped.get_price_history("AAPL")
    assert history.bars[0].close == Decimal("9")  # fallback


async def test_fallback_kicks_in_when_primary_raises():
    wrapped = PriceFallbackMarketData(_Primary(raises=True), _Fallback())
    history = await wrapped.get_price_history("AAPL")
    assert history.bars[0].close == Decimal("9")  # fallback


async def test_fallback_delegates_other_methods_to_primary():
    wrapped = PriceFallbackMarketData(_Primary(), _Fallback())
    assert wrapped.fallback_marker == "primary"  # __getattr__ delegation
