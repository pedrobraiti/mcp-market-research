from datetime import date
from decimal import Decimal

from scout.adapters.coinpaprika import CoinpaprikaAssets

_SEARCH = {
    "currencies": [
        {"id": "btc-bitcoin", "name": "Bitcoin", "symbol": "BTC", "rank": 1},
    ]
}

_TICKER = {
    "id": "btc-bitcoin",
    "name": "Bitcoin",
    "symbol": "BTC",
    "rank": 1,
    "circulating_supply": 19700000,
    "total_supply": 19700000,
    "max_supply": 21000000,
    "quotes": {
        "USD": {
            "price": 67000.0,
            "market_cap": 1320000000000,
            "volume_24h": 30000000000,
            "ath_price": 73000.0,
            "ath_date": "2024-03-14T00:00:00Z",
            "percent_from_price_ath": -8.2,
        }
    },
}


def _source(search=_SEARCH, ticker=_TICKER):
    async def _fetch(url: str):
        if "search" in url:
            return search
        return ticker

    return CoinpaprikaAssets(fetch_json=_fetch)


async def test_get_profile_builds_model():
    profile = await _source().get_profile("BTC")
    assert profile is not None
    assert profile.base == "BTC"
    assert profile.source_id == "btc-bitcoin"
    assert profile.rank == 1
    assert profile.market_cap_usd == Decimal("1320000000000")
    assert profile.max_supply == Decimal("21000000")
    assert profile.ath_date == date(2024, 3, 14)
    assert profile.percent_from_ath == Decimal("-8.2")
    # Derived tokenomics: circulating == total → float 1.0; 19.7M/21M minted; ~6.6% overhang.
    assert profile.float_ratio == Decimal("1.0000")
    assert profile.issuance_progress == Decimal("0.9381")
    assert profile.future_dilution == Decimal("0.0660")


async def test_get_profile_uncapped_supply_yields_null_max_ratios():
    ticker = {
        **_TICKER,
        "circulating_supply": 120000000,
        "total_supply": 120000000,
        "max_supply": 0,  # uncapped (e.g. ETH) → max-based ratios must be null, not a divide error
    }
    profile = await _source(ticker=ticker).get_profile("ETH")
    assert profile.float_ratio == Decimal("1.0000")
    assert profile.issuance_progress is None  # no max supply to measure against
    assert profile.future_dilution is None


async def test_get_profile_prefers_exact_symbol_match():
    search = {
        "currencies": [
            {"id": "btc-some-clone", "name": "Bitcoin Clone", "symbol": "BTCC", "rank": 50},
            {"id": "btc-bitcoin", "name": "Bitcoin", "symbol": "BTC", "rank": 1},
        ]
    }

    captured = {}

    async def _fetch(url: str):
        if "search" in url:
            return search
        captured["ticker_url"] = url
        return _TICKER

    profile = await CoinpaprikaAssets(fetch_json=_fetch).get_profile("BTC")
    assert "btc-bitcoin" in captured["ticker_url"]  # exact symbol, lowest rank
    assert profile.base == "BTC"


async def test_get_profile_none_when_no_match():
    profile = await _source(search={"currencies": []}).get_profile("NOTACOIN")
    assert profile is None


async def test_search_returns_matches_sorted_by_rank():
    search = {
        "currencies": [
            {"id": "eth-ethereum", "name": "Ethereum", "symbol": "ETH", "rank": 2},
            {"id": "etc-classic", "name": "Ethereum Classic", "symbol": "ETC", "rank": 30},
        ]
    }

    async def _fetch(url: str):
        return search

    result = await CoinpaprikaAssets(fetch_json=_fetch).search("eth", limit=5)
    assert result.query == "eth"
    assert [m.base for m in result.matches] == ["ETH", "ETC"]  # rank-sorted
    assert result.matches[0].source_id == "eth-ethereum"


async def test_search_empty_query():
    async def _fetch(url: str):
        raise AssertionError("should not fetch on empty query")

    result = await CoinpaprikaAssets(fetch_json=_fetch).search("  ")
    assert result.matches == []
