from decimal import Decimal

from scout.adapters.onchain import OnChainNetwork

_BTC = {
    "fees": {"fastestFee": 12, "halfHourFee": 8, "hourFee": 5},
    "hashrate": {"currentHashrate": 6.5e20, "currentDifficulty": 9.0e13},
    "difficulty": {"difficultyChange": 2.3},
}

_ETH_STATS = {
    "total_addresses": "663000000",
    "total_transactions": "3500000000",
    "gas_prices": {"slow": 1.0, "average": 2.5, "fast": 4.0},
    "network_utilization_percentage": 55.2,
    "average_block_time": 12050,
}


def _btc_source():
    async def _fetch(url: str):
        if "fees/recommended" in url:
            return _BTC["fees"]
        if "hashrate" in url:
            return _BTC["hashrate"]
        if "difficulty-adjustment" in url:
            return _BTC["difficulty"]
        raise AssertionError(url)

    return OnChainNetwork(fetch_json=_fetch)


async def test_bitcoin_metrics():
    result = await _btc_source().get_onchain("BTC")
    assert result.asset == "BTC"
    assert result.source == "mempool.space"
    by_name = {m.name: m for m in result.metrics}
    assert by_name["fastest_fee"].value == Decimal("12")
    assert by_name["fastest_fee"].unit == "sat/vB"
    assert by_name["difficulty_change"].value == Decimal("2.3")


async def test_ethereum_metrics():
    async def _fetch(url: str):
        assert "blockscout" in url
        return _ETH_STATS

    result = await OnChainNetwork(fetch_json=_fetch).get_onchain("ETH")
    assert result.asset == "ETH"
    by_name = {m.name: m for m in result.metrics}
    assert by_name["total_addresses"].value == Decimal("663000000")
    assert by_name["gas_average"].value == Decimal("2.5")
    assert by_name["network_utilization"].value == Decimal("55.2")


async def test_unknown_asset_returns_note():
    async def _fetch(url: str):
        raise AssertionError("should not fetch")

    result = await OnChainNetwork(fetch_json=_fetch).get_onchain("DOGE")
    assert result.metrics == []
    assert "No keyless on-chain source" in result.note


async def test_bitcoin_partial_failure_keeps_other_metrics():
    async def _fetch(url: str):
        if "hashrate" in url:
            raise RuntimeError("down")
        if "fees/recommended" in url:
            return _BTC["fees"]
        if "difficulty-adjustment" in url:
            return _BTC["difficulty"]
        raise AssertionError(url)

    result = await OnChainNetwork(fetch_json=_fetch).get_onchain("BTC")
    names = {m.name for m in result.metrics}
    assert "fastest_fee" in names
    assert "hashrate" not in names  # dropped on failure
