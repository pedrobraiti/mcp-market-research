from scout.adapters.apewisdom import ApeWisdomBuzz

_RESPONSE = {
    "results": [
        {"rank": 1, "ticker": "NVDA", "name": "NVIDIA", "mentions": 500, "mentions_24h_ago": 420,
         "upvotes": 9000, "rank_24h_ago": 2},
        {"rank": 2, "ticker": "TSLA", "name": "Tesla", "mentions": 300, "mentions_24h_ago": 350,
         "upvotes": 4000, "rank_24h_ago": 1},
    ]
}


def _source():
    async def _fetch(url: str) -> dict:
        return _RESPONSE

    return ApeWisdomBuzz(fetch_json=_fetch)


async def test_buzz_returns_trending_list():
    result = await _source().get_buzz(limit=5)
    assert result.symbol is None
    assert [i.symbol for i in result.items] == ["NVDA", "TSLA"]
    assert result.items[0].mentions == 500
    assert result.items[0].rank_24h_ago == 2


async def test_buzz_for_specific_symbol():
    result = await _source().get_buzz("nvda")
    assert result.symbol == "NVDA"
    assert len(result.items) == 1
    assert result.items[0].mentions == 500


async def test_buzz_symbol_not_trending():
    result = await _source().get_buzz("AAPL")
    assert result.items == []
    assert "not in the current Reddit trending list" in result.note


_CRYPTO_RESPONSE = {
    "results": [
        {"rank": 1, "ticker": "BTC.X", "name": "Bitcoin", "mentions": 210,
         "mentions_24h_ago": 180, "upvotes": 5000, "rank_24h_ago": 1},
        {"rank": 2, "ticker": "ETH.X", "name": "Ethereum", "mentions": 150,
         "mentions_24h_ago": 160, "upvotes": 3000, "rank_24h_ago": 2},
    ]
}


def _crypto_source():
    captured = {}

    async def _fetch(url: str) -> dict:
        captured["url"] = url
        return _CRYPTO_RESPONSE

    return ApeWisdomBuzz(fetch_json=_fetch, filter_name="all-crypto", strip_suffix=True), captured


async def test_crypto_filter_strips_suffix_and_uses_crypto_url():
    source, captured = _crypto_source()
    result = await source.get_buzz(limit=5)
    assert "all-crypto" in captured["url"]
    assert [i.symbol for i in result.items] == ["BTC", "ETH"]  # ".X" suffix stripped


async def test_crypto_buzz_symbol_lookup_matches_stripped_base():
    source, _ = _crypto_source()
    result = await source.get_buzz("btc")
    assert result.symbol == "BTC"
    assert len(result.items) == 1
    assert result.items[0].mentions == 210
