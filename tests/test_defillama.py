from decimal import Decimal

from scout.adapters.defillama import DefiLlamaDefi

_CHAINS = [
    {"name": "Ethereum", "tvl": 60000000000},
    {"name": "Solana", "tvl": 8000000000},
    {"name": "Tron", "tvl": 5000000000},
]

_PROTOCOL = {
    "name": "Aave",
    "category": "Lending",
    "currentChainTvls": {"Ethereum": 10000000000, "Polygon": 500000000, "Ethereum-borrowed": 99},
}

_STABLES = {
    "peggedAssets": [
        {
            "symbol": "USDT",
            "name": "Tether",
            "pegType": "peggedUSD",
            "pegMechanism": "fiat-backed",
            "price": 1.001,
            "circulating": {"peggedUSD": 120000000000},
        },
        {
            "symbol": "DAI",
            "name": "Dai",
            "pegType": "peggedUSD",
            "pegMechanism": "crypto-backed",
            "price": 0.998,
            "circulating": {"peggedUSD": 5000000000},
        },
    ]
}

_YIELDS = {
    "data": [
        {"project": "aave-v3", "chain": "Ethereum", "symbol": "USDC", "tvlUsd": 2e9, "apy": 4.5,
         "apyBase": 4.0, "apyReward": 0.5},
        {"project": "curve", "chain": "Ethereum", "symbol": "3POOL", "tvlUsd": 5e8, "apy": 9.0,
         "apyBase": 9.0, "apyReward": None},
        {"project": "dust", "chain": "Solana", "symbol": "X", "tvlUsd": 1000, "apy": 999.0},
    ]
}


async def test_tvl_chains():
    async def _fetch(url: str):
        return _CHAINS

    result = await DefiLlamaDefi(fetch_json=_fetch).get_tvl()
    assert result.scope == "chains"
    assert result.items[0].name == "Ethereum"
    assert result.total_tvl_usd == Decimal("73000000000")


async def test_tvl_protocol_excludes_borrowed():
    async def _fetch(url: str):
        assert "protocol/aave" in url
        return _PROTOCOL

    result = await DefiLlamaDefi(fetch_json=_fetch).get_tvl("aave")
    names = [i.name for i in result.items]
    assert "Ethereum-borrowed" not in names
    assert result.items[0].name == "Ethereum"


async def test_stablecoins_peg_deviation():
    async def _fetch(url: str):
        return _STABLES

    result = await DefiLlamaDefi(fetch_json=_fetch).get_stablecoins()
    assert result.total_circulating_usd == Decimal("125000000000")
    usdt = result.items[0]
    assert usdt.symbol == "USDT"
    assert usdt.peg_deviation == Decimal("0.001")


async def test_yields_filters_and_sorts():
    async def _fetch(url: str):
        return _YIELDS

    result = await DefiLlamaDefi(fetch_json=_fetch).get_yields(min_tvl=1_000_000)
    # dust pool (1000 < 1M) excluded; sorted by APY desc → curve(9) before aave(4.5)
    symbols = [p.symbol for p in result.pools]
    assert symbols == ["3POOL", "USDC"]


async def test_yields_chain_filter():
    async def _fetch(url: str):
        return _YIELDS

    result = await DefiLlamaDefi(fetch_json=_fetch).get_yields(chain="solana", min_tvl=100)
    assert [p.project for p in result.pools] == ["dust"]
