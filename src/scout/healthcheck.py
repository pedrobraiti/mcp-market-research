"""Quick smoke test: fetch a known symbol so you can confirm the data source works.

Run with ``python -m scout.healthcheck`` or the ``scout-healthcheck`` script. Hits the
network (yfinance), so it is a manual check, not part of the offline test suite.
"""

from __future__ import annotations

import asyncio

from .server.services import build_services


async def _run(symbol: str) -> int:
    services = build_services()
    snapshot = await services.market_data.get_snapshot(symbol)
    if snapshot is None:
        print(f"[FAIL] Could not resolve {symbol} — data source may be down or symbol invalid.")
        return 1
    print(f"[OK] {snapshot.symbol} {snapshot.name or ''}")
    print(f"     price={snapshot.price} change%={snapshot.change_percent} pe={snapshot.pe_ratio}")
    dividends = await services.market_data.get_dividends(symbol)
    if dividends is not None:
        print(
            f"     dividend trailing_yield={dividends.trailing_yield} "
            f"streak={dividends.growth_streak_years}y had_cut={dividends.had_cut}"
        )
    return 0


def main() -> None:
    import sys

    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    raise SystemExit(asyncio.run(_run(symbol)))


if __name__ == "__main__":
    main()
