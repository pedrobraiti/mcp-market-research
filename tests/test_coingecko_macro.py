from decimal import Decimal

from scout.adapters.coingecko import CoinGeckoMacro

_GLOBAL = {
    "data": {
        "total_market_cap": {"usd": 2.4e12},
        "total_volume": {"usd": 9e10},
        "market_cap_percentage": {"btc": 54.2, "eth": 17.1},
        "active_cryptocurrencies": 13500,
        "market_cap_change_percentage_24h_usd": -1.8,
    }
}

_GLOBAL_DEFI = {"data": {"defi_market_cap": "95000000000", "defi_dominance": "4.0"}}

_CATEGORIES = [
    {"name": "Layer 1", "market_cap": 1.2e12, "market_cap_change_24h": -1.5,
     "volume_24h": 4e10, "top_3_coins_id": ["bitcoin", "ethereum", "solana"]},
    {"name": "DeFi", "market_cap": 9e10, "market_cap_change_24h": 2.0, "volume_24h": 5e9,
     "top_3_coins_id": ["uniswap", "aave", "maker"]},
]


async def test_macro_merges_global_and_defi():
    async def _fetch(url: str):
        if url.endswith("/global"):
            return _GLOBAL
        if "decentralized_finance_defi" in url:
            return _GLOBAL_DEFI
        raise AssertionError(url)

    result = await CoinGeckoMacro(fetch_json=_fetch).get_macro()
    assert result.total_market_cap_usd == Decimal("2400000000000")
    assert result.btc_dominance == Decimal("54.2")
    assert result.defi_market_cap_usd == Decimal("95000000000")
    assert result.active_cryptocurrencies == 13500


async def test_macro_tolerates_defi_failure():
    async def _fetch(url: str):
        if url.endswith("/global"):
            return _GLOBAL
        raise RuntimeError("429")

    result = await CoinGeckoMacro(fetch_json=_fetch).get_macro()
    assert result.btc_dominance == Decimal("54.2")  # global still parsed
    assert result.defi_market_cap_usd is None  # defi failed, left null


async def test_sectors():
    async def _fetch(url: str):
        return _CATEGORIES

    result = await CoinGeckoMacro(fetch_json=_fetch).get_sectors()
    assert [c.name for c in result.categories] == ["Layer 1", "DeFi"]
    assert result.categories[0].top_3_coins == ["bitcoin", "ethereum", "solana"]
    assert result.categories[1].market_cap_change_24h == Decimal("2.0")
