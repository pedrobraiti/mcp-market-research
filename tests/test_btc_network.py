from datetime import UTC, datetime
from decimal import Decimal

from scout.adapters.btc_network import BtcNetworkData

_BASE_TS = 1_700_000_000


class _Resp:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class _HttpError(Exception):
    def __init__(self, status_code: int) -> None:
        self.response = _Resp(status_code)
        super().__init__(f"HTTP {status_code}")


def _chart(value: float, n: int = 1) -> dict:
    return {
        "unit": "x",
        "values": [{"x": _BASE_TS + i * 86_400, "y": value} for i in range(n)],
    }


_FEES = {
    "fastestFee": 20,
    "halfHourFee": 15,
    "hourFee": 10,
    "economyFee": 5,
    "minimumFee": 1,
}

_DIFFICULTY = {
    "progressPercent": 42.5,
    "difficultyChange": 3.1,
    "estimatedRetargetDate": 1_700_500_000_000,
    "remainingBlocks": 800,
}


def _all_charts(market_cap: float, tx_volume: float, points: int = 1):
    async def _fetch(url: str):
        if "charts/hash-rate" in url:
            return _chart(200, n=points)
        if "charts/miners-revenue" in url:
            return _chart(5e7, n=points)
        if "charts/n-transactions" in url:
            return _chart(400000, n=points)
        if "charts/estimated-transaction-volume-usd" in url:
            return _chart(tx_volume, n=points)
        if "charts/market-cap" in url:
            return _chart(market_cap, n=points)
        if "fees/recommended" in url:
            return _FEES
        if "difficulty-adjustment" in url:
            return _DIFFICULTY
        raise AssertionError(f"unexpected url {url}")

    return _fetch


async def test_nvt_computed_and_nvt_90d_null_under_90_points():
    result = await BtcNetworkData(fetch_json=_all_charts(1000, 100)).get_network()
    assert result.market_cap_usd == Decimal("1000")
    assert result.tx_volume_usd == Decimal("100")
    assert result.nvt == Decimal("10")  # 1000 / 100
    assert result.nvt_90d is None  # single point < 90 → not enough to smooth
    assert result.fee_fastest == Decimal("20")
    assert result.difficulty_change_pct == Decimal("3.1")
    assert result.estimated_retarget_date is not None
    assert result.partial is False
    assert result.source_status is None


async def test_nvt_90d_computed_with_enough_points():
    result = await BtcNetworkData(fetch_json=_all_charts(1000, 100, points=90)).get_network()
    assert result.nvt_90d == Decimal("10")  # avg of 90 points (all 100) → 1000 / 100
    assert len(result.history) > 0
    assert result.history[-1].hash_rate == Decimal("200")
    assert result.history[-1].nvt == Decimal("10")  # history NVT must populate, not just headline


async def test_history_nvt_populates_when_market_cap_is_intraday():
    # Real Blockchain.com behaviour: hash-rate/tx-volume are midnight-aligned but market-cap uses
    # intraday timestamps. An exact-ts join drops every history NVT; the date join must recover it.
    midnight = int(datetime(2024, 1, 1, tzinfo=UTC).timestamp())  # a true midnight grid

    async def _fetch(url: str):
        if "charts/hash-rate" in url:
            return {"values": [{"x": midnight + i * 86_400, "y": 200} for i in range(5)]}
        if "charts/estimated-transaction-volume-usd" in url:
            return {"values": [{"x": midnight + i * 86_400, "y": 100} for i in range(5)]}
        if "charts/market-cap" in url:  # same days, shifted to noon (stays within the day)
            return {"values": [{"x": midnight + i * 86_400 + 43_200, "y": 1000} for i in range(5)]}
        if "charts/miners-revenue" in url:
            return _chart(5e7, n=5)
        if "charts/n-transactions" in url:
            return _chart(400000, n=5)
        if "fees/recommended" in url:
            return _FEES
        if "difficulty-adjustment" in url:
            return _DIFFICULTY
        raise AssertionError(f"unexpected url {url}")

    result = await BtcNetworkData(fetch_json=_fetch).get_network()
    assert result.history, "history should not be empty"
    assert all(p.nvt == Decimal("10") for p in result.history)  # 1000 / 100, joined by date


async def test_mempool_leg_failure_keeps_fundamentals():
    async def _fetch(url: str):
        if "mempool.space" in url:
            raise _HttpError(429)
        if "charts/market-cap" in url:
            return _chart(1000)
        if "charts/estimated-transaction-volume-usd" in url:
            return _chart(100)
        if "charts/hash-rate" in url:
            return _chart(200)
        if "charts/miners-revenue" in url:
            return _chart(5e7)
        if "charts/n-transactions" in url:
            return _chart(400000)
        raise AssertionError(f"unexpected url {url}")

    result = await BtcNetworkData(fetch_json=_fetch, retry_base_delay=0).get_network()
    assert result.nvt == Decimal("10")  # fundamentals present
    assert result.fee_fastest is None  # fee market unavailable
    assert result.difficulty_change_pct is None
    assert result.partial is True
    assert result.source_status is not None and "rate_limited" in result.source_status
    assert "mempool.space" in result.note


async def test_blockchain_leg_failure_keeps_fee_market():
    async def _fetch(url: str):
        if "api.blockchain.info" in url:
            raise _HttpError(429)
        if "fees/recommended" in url:
            return _FEES
        if "difficulty-adjustment" in url:
            return _DIFFICULTY
        raise AssertionError(f"unexpected url {url}")

    result = await BtcNetworkData(fetch_json=_fetch, retry_base_delay=0).get_network()
    assert result.market_cap_usd is None  # fundamentals unavailable
    assert result.nvt is None
    assert result.fee_fastest == Decimal("20")  # fee market present
    assert result.difficulty_change_pct == Decimal("3.1")
    assert result.partial is True
    assert result.source_status is not None and "rate_limited" in result.source_status
    assert "Blockchain.com" in result.note
