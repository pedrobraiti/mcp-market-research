"""DefiLlama implementation of ``DefiSource`` — keyless DeFi TVL, stablecoins and yields.

DefiLlama's open hosts (api.llama.fi / stablecoins.llama.fi / yields.llama.fi) need no key and have
generous limits. Some responses are multi-MB (all protocols / all pools), so results are filtered
and capped here. Raw ecosystem facts (TVL, peg, APY), never a verdict.

The JSON fetch is injected so the unit tests run fully offline.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from decimal import Decimal, InvalidOperation
from typing import Any

from ...domain.models import (
    DefiOverview,
    DefiTvlItem,
    DefiYields,
    StablecoinItem,
    StablecoinSupply,
    YieldPool,
)

_CHAINS_URL = "https://api.llama.fi/v2/chains"
_PROTOCOL_URL = "https://api.llama.fi/protocol/{slug}"
_STABLES_URL = "https://stablecoins.llama.fi/stablecoins?includePrices=true"
_YIELDS_URL = "https://yields.llama.fi/pools"


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


class DefiLlamaDefi:
    def __init__(
        self,
        fetch_json: Callable[[str], Awaitable[Any]] | None = None,
        timeout: float = 20.0,
    ) -> None:
        self._timeout = timeout
        self._fetch_json = fetch_json or self._default_fetch_json

    async def _default_fetch_json(self, url: str) -> Any:
        import httpx

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_tvl(self, slug: str | None = None) -> DefiOverview:
        if slug:
            data = await self._fetch_json(_PROTOCOL_URL.format(slug=slug.strip().lower()))
            chain_tvls = (data or {}).get("currentChainTvls") or {}
            items = [
                DefiTvlItem(name=chain, tvl_usd=_dec(tvl))
                for chain, tvl in chain_tvls.items()
                if not str(chain).endswith("-borrowed")
            ]
            items.sort(key=lambda i: i.tvl_usd or Decimal(0), reverse=True)
            total = sum((i.tvl_usd or Decimal(0)) for i in items) or None
            return DefiOverview(scope=slug, total_tvl_usd=total, items=items[:30])

        chains = await self._fetch_json(_CHAINS_URL)
        rows = [c for c in (chains or []) if isinstance(c, dict)]
        items = [DefiTvlItem(name=c.get("name"), tvl_usd=_dec(c.get("tvl"))) for c in rows]
        items.sort(key=lambda i: i.tvl_usd or Decimal(0), reverse=True)
        total = sum((i.tvl_usd or Decimal(0)) for i in items) or None
        return DefiOverview(scope="chains", total_tvl_usd=total, items=items[:30])

    async def get_stablecoins(self) -> StablecoinSupply:
        data = await self._fetch_json(_STABLES_URL)
        assets = [a for a in ((data or {}).get("peggedAssets") or []) if isinstance(a, dict)]
        items: list[StablecoinItem] = []
        total = Decimal(0)
        for asset in assets:
            circ = _dec((asset.get("circulating") or {}).get("peggedUSD"))
            price = _dec(asset.get("price"))
            if circ is not None:
                total += circ
            items.append(
                StablecoinItem(
                    symbol=asset.get("symbol"),
                    name=asset.get("name"),
                    peg_type=asset.get("pegType"),
                    peg_mechanism=asset.get("pegMechanism"),
                    price=price,
                    peg_deviation=(price - Decimal(1)) if price is not None else None,
                    circulating_usd=circ,
                )
            )
        items.sort(key=lambda i: i.circulating_usd or Decimal(0), reverse=True)
        return StablecoinSupply(total_circulating_usd=total or None, items=items[:30])

    async def get_yields(
        self, chain: str | None = None, project: str | None = None, min_tvl: float = 1_000_000
    ) -> DefiYields:
        data = await self._fetch_json(_YIELDS_URL)
        pools = [p for p in ((data or {}).get("data") or []) if isinstance(p, dict)]
        chain_f = chain.strip().lower() if chain else None
        project_f = project.strip().lower() if project else None
        floor = _dec(min_tvl) or Decimal(0)
        out: list[YieldPool] = []
        for pool in pools:
            tvl = _dec(pool.get("tvlUsd"))
            if tvl is None or tvl < floor:
                continue
            if chain_f and str(pool.get("chain", "")).lower() != chain_f:
                continue
            if project_f and str(pool.get("project", "")).lower() != project_f:
                continue
            out.append(
                YieldPool(
                    project=pool.get("project"),
                    chain=pool.get("chain"),
                    symbol=pool.get("symbol"),
                    tvl_usd=tvl,
                    apy=_dec(pool.get("apy")),
                    apy_base=_dec(pool.get("apyBase")),
                    apy_reward=_dec(pool.get("apyReward")),
                )
            )
        out.sort(key=lambda p: p.apy or Decimal(0), reverse=True)
        return DefiYields(pools=out[:25])
