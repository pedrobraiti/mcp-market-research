from datetime import UTC, datetime
from decimal import Decimal

from scout.adapters.deribit import DeribitVol


def _ms(y, m, d):
    return int(datetime(y, m, d, tzinfo=UTC).timestamp() * 1000)


async def _fetch(url: str):
    if "get_index_price" in url:
        assert "btcdvol_usdc" in url
        return {"result": {"index_price": 45.45}}
    if "get_volatility_index_data" in url:
        return {
            "result": {
                "data": [
                    [_ms(2026, 6, 24), 44.0, 46.0, 43.5, 45.0],
                    [_ms(2026, 6, 25), 45.0, 47.0, 44.5, 45.45],
                ]
            }
        }
    raise AssertionError(url)


async def test_dvol_current_and_history():
    result = await DeribitVol(fetch_json=_fetch, now_ms=_ms(2026, 6, 25)).get_implied_vol("BTC")
    assert result.asset == "BTC"
    assert result.dvol_current == Decimal("45.45")
    assert len(result.history) == 2
    assert result.history[-1].close == Decimal("45.45")


async def test_unsupported_asset_note():
    async def _f(url: str):
        raise AssertionError("should not fetch")

    result = await DeribitVol(fetch_json=_f).get_implied_vol("SOL")
    assert result.dvol_current is None
    assert "BTC and ETH only" in result.note


async def test_partial_failure_index_only():
    async def _f(url: str):
        if "get_volatility_index_data" in url:
            raise RuntimeError("down")
        return {"result": {"index_price": 50.0}}

    result = await DeribitVol(fetch_json=_f, now_ms=_ms(2026, 6, 25)).get_implied_vol("ETH")
    assert result.dvol_current == Decimal("50.0")
    assert result.history == []
