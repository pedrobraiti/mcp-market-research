"""On-chain network-health metrics — keyless, per chain.

BTC comes from mempool.space (fees, hashrate, difficulty); ETH from a public Blockscout instance
(addresses, transactions, gas, network utilization). Both keyless. Heterogeneous chains, so the
result is a labelled list of metrics — raw on-chain facts, never a verdict.

The JSON fetch is injected so the unit tests run fully offline.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from decimal import Decimal, InvalidOperation
from typing import Any

from ...domain.models import CryptoOnChain, OnChainMetric

_MEMPOOL = "https://mempool.space/api"
_BLOCKSCOUT = "https://eth.blockscout.com/api/v2"


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


class OnChainNetwork:
    def __init__(
        self,
        fetch_json: Callable[[str], Awaitable[Any]] | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._timeout = timeout
        self._fetch_json = fetch_json or self._default_fetch_json

    async def _default_fetch_json(self, url: str) -> Any:
        import httpx

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_onchain(self, asset: str = "BTC") -> CryptoOnChain:
        token = asset.strip().upper()
        if token in ("BTC", "BITCOIN"):
            return await self._bitcoin()
        if token in ("ETH", "ETHEREUM"):
            return await self._ethereum()
        return CryptoOnChain(
            asset=token,
            source="none",
            note=f"No keyless on-chain source wired for {token} (BTC and ETH supported).",
        )

    async def _bitcoin(self) -> CryptoOnChain:
        fees, hashrate, difficulty = await asyncio.gather(
            self._fetch_json(f"{_MEMPOOL}/v1/fees/recommended"),
            self._fetch_json(f"{_MEMPOOL}/v1/mining/hashrate/3d"),
            self._fetch_json(f"{_MEMPOOL}/v1/difficulty-adjustment"),
            return_exceptions=True,
        )
        metrics: list[OnChainMetric] = []
        if isinstance(fees, dict):
            sat = "sat/vB"
            metrics += [
                OnChainMetric(name="fastest_fee", value=_dec(fees.get("fastestFee")), unit=sat),
                OnChainMetric(name="half_hour_fee", value=_dec(fees.get("halfHourFee")), unit=sat),
                OnChainMetric(name="hour_fee", value=_dec(fees.get("hourFee")), unit=sat),
            ]
        if isinstance(hashrate, dict):
            metrics += [
                OnChainMetric(
                    name="hashrate", value=_dec(hashrate.get("currentHashrate")), unit="H/s"
                ),
                OnChainMetric(
                    name="difficulty", value=_dec(hashrate.get("currentDifficulty")), unit=None
                ),
            ]
        if isinstance(difficulty, dict):
            metrics.append(
                OnChainMetric(
                    name="difficulty_change",
                    value=_dec(difficulty.get("difficultyChange")),
                    unit="%",
                )
            )
        return CryptoOnChain(asset="BTC", source="mempool.space", metrics=metrics)

    async def _ethereum(self) -> CryptoOnChain:
        stats = await self._fetch_json(f"{_BLOCKSCOUT}/stats")
        if not isinstance(stats, dict):
            return CryptoOnChain(asset="ETH", source="blockscout", note="No stats returned.")
        gas = stats.get("gas_prices") or {}
        metrics = [
            OnChainMetric(name="total_addresses", value=_dec(stats.get("total_addresses"))),
            OnChainMetric(name="total_transactions", value=_dec(stats.get("total_transactions"))),
            OnChainMetric(name="gas_average", value=_dec(gas.get("average")), unit="gwei"),
            OnChainMetric(name="gas_fast", value=_dec(gas.get("fast")), unit="gwei"),
            OnChainMetric(
                name="network_utilization",
                value=_dec(stats.get("network_utilization_percentage")),
                unit="%",
            ),
            OnChainMetric(
                name="average_block_time",
                value=_dec(stats.get("average_block_time")),
                unit="ms",
            ),
        ]
        return CryptoOnChain(asset="ETH", source="blockscout", metrics=metrics)
