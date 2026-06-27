from datetime import UTC, datetime, timedelta
from decimal import Decimal

from scout.domain.models import (
    CryptoAssetProfile,
    CryptoBar,
    CryptoDerivatives,
    CryptoFearGreed,
    CryptoOnChain,
    CryptoPriceHistory,
    CryptoQuote,
)
from scout.research import (
    build_crypto_comparison,
    build_crypto_correlation,
    build_crypto_dossier,
    build_crypto_relative_strength,
)


def _history(base: str, closes: list[float]) -> CryptoPriceHistory:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    bars = [
        CryptoBar(timestamp=start + timedelta(days=i), close=Decimal(str(c)))
        for i, c in enumerate(closes)
    ]
    return CryptoPriceHistory(
        symbol=f"{base}/USDT", base=base, quote="USDT", exchange="binance",
        timeframe="1d", bars=bars,
    )


class StubMarket:
    def __init__(self, histories=None, quotes=None):
        self._histories = histories or {}
        self._quotes = quotes or {}

    async def get_quote(self, symbol):
        base = symbol.split("/")[0].upper()
        return self._quotes.get(base)

    async def get_price_history(self, symbol, timeframe="1d", limit=200, as_of=None):
        base = symbol.split("/")[0].upper()
        return self._histories.get(base)

    async def get_movers(self, category="gainers", limit=20):  # unused here
        ...

    async def get_order_book(self, symbol, limit=20):  # unused here
        ...


class StubAssets:
    def __init__(self, profiles=None):
        self._profiles = profiles or {}

    async def get_profile(self, base):
        return self._profiles.get(base.upper())

    async def search(self, query, limit=10):  # unused here
        ...


class StubSentiment:
    async def get_fear_greed(self, days=30):
        return CryptoFearGreed(value=20, classification="Extreme Fear")


class StubDerivatives:
    async def get_derivatives(self, base):
        return CryptoDerivatives(base=base, venues=[])


class StubOnChain:
    async def get_onchain(self, asset="BTC"):
        return CryptoOnChain(asset=asset, source="mempool.space", metrics=[])


async def test_compare_merges_quote_and_profile():
    market = StubMarket(
        quotes={
            "BTC": CryptoQuote(symbol="BTC/USDT", base="BTC", quote="USDT", exchange="binance",
                               last=Decimal("60000"), change_percent_24h=Decimal("2.0")),
        }
    )
    assets = StubAssets(
        profiles={"BTC": CryptoAssetProfile(base="BTC", rank=1, market_cap_usd=Decimal("1.2e12"))}
    )
    result = await build_crypto_comparison(market, assets, ["BTC", "DOGE"])
    rows = {r.base: r for r in result.items}
    assert rows["BTC"].last == Decimal("60000")
    assert rows["BTC"].rank == 1
    assert rows["DOGE"].note == "data unavailable"  # no quote/profile


async def test_correlation_perfectly_correlated():
    market = StubMarket(
        histories={
            "BTC": _history("BTC", [100, 110, 121, 130]),
            "ETH": _history("ETH", [20, 22, 24.2, 26]),  # exactly 0.2x BTC → identical returns
        }
    )
    result = await build_crypto_correlation(market, ["BTC", "ETH"], "1d", 120)
    assert len(result.pairs) == 1
    assert result.pairs[0].correlation == Decimal("1.0")


async def test_correlation_needs_two_series():
    market = StubMarket(histories={"BTC": _history("BTC", [1, 2, 3])})
    result = await build_crypto_correlation(market, ["BTC", "ETH"], "1d", 120)
    assert result.pairs == []
    assert "at least two" in result.note


async def test_relative_strength_vs_btc():
    market = StubMarket(
        histories={
            "BTC": _history("BTC", [100, 110]),  # +10%
            "SOL": _history("SOL", [100, 130]),  # +30% → excess +20
            "ADA": _history("ADA", [100, 105]),  # +5% → excess -5
        }
    )
    result = await build_crypto_relative_strength(market, ["SOL", "ADA"], "BTC", "1d", 90)
    assert result.benchmark == "BTC"
    assert result.rows[0].symbol == "SOL"  # sorted strongest first
    assert result.rows[0].excess_vs_benchmark == Decimal("20.0")
    assert result.rows[1].excess_vs_benchmark == Decimal("-5.0")


async def test_relative_strength_notes_dropped_symbol():
    market = StubMarket(histories={"BTC": _history("BTC", [100, 110])})  # only benchmark has data
    result = await build_crypto_relative_strength(market, ["SOL"], "BTC", "1d", 90)
    assert result.rows == []
    assert any("SOL" in n for n in result.notes)  # missing symbol is reported, not silently dropped


async def test_dossier_full_fans_out_and_computes_technicals():
    closes = [float(100 + i) for i in range(60)]  # enough bars for some indicators
    market = StubMarket(
        histories={"BTC": _history("BTC", closes)},
        quotes={"BTC": CryptoQuote(symbol="BTC/USDT", base="BTC", quote="USDT",
                                   exchange="binance", last=Decimal("159"))},
    )
    assets = StubAssets(profiles={"BTC": CryptoAssetProfile(base="BTC", rank=1)})
    dossier = await build_crypto_dossier(
        market, assets, StubSentiment(), StubDerivatives(), StubOnChain(), "BTC", "full"
    )
    assert dossier.base == "BTC"
    assert dossier.quote_data.last == Decimal("159")
    assert dossier.profile.rank == 1
    assert dossier.fear_greed.value == 20
    assert dossier.technicals is not None
    assert dossier.technicals.rsi_14 is not None


async def test_dossier_summary_skips_heavy_reads():
    market = StubMarket(
        quotes={"BTC": CryptoQuote(symbol="BTC/USDT", base="BTC", quote="USDT", exchange="binance")}
    )
    assets = StubAssets(profiles={"BTC": CryptoAssetProfile(base="BTC")})
    dossier = await build_crypto_dossier(
        market, assets, StubSentiment(), StubDerivatives(), StubOnChain(), "BTC", "summary"
    )
    assert dossier.quote_data is not None
    assert dossier.technicals is None
    assert dossier.derivatives is None
