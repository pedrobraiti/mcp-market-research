"""Stablecoin peg-deviation — keyless, CCXT-derived (Kraken ``<SYM>/USD`` spot).

Deviation of major stablecoins from $1 is the PRICE axis of stablecoin health (a depeg is a
market-wide tail trigger), complementing the SUPPLY axis already covered by ``stablecoin_supply``.
Kraken is the fixed default venue because it lists USDT, USDC and DAI against USD.

Per venue this reuses ``CcxtMarketData`` (and its shared, rate-limited exchange — see
``market_data._shared_exchange``); a ``CcxtMarketData`` factory is injected so the unit tests run
fully offline, with no network and no ccxt import.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from ...domain.models import StablecoinPeg, StablecoinPegItem
from ..retry import SourceUnavailable, unavailable_status
from .market_data import CcxtMarketData

CcxtMarketFactory = Callable[[str], CcxtMarketData]

_DEFAULT_SYMBOLS = ("USDT", "USDC", "DAI")
_DEFAULT_VENUE = "kraken"
_PEG_QUOTE_CCY = "USD"
_DEPEG_BPS_THRESHOLD = 50  # |deviation| beyond this (in basis points) flags a depeg
_BPS_PER_UNIT = 10000


def _quantize(value: Decimal | None, places: int) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)


class CcxtStablecoinPeg:
    def __init__(
        self,
        market_factory: CcxtMarketFactory | None = None,
        default_venue: str = _DEFAULT_VENUE,
        timeout: float = 15.0,
    ) -> None:
        self._default_venue = default_venue
        self._timeout = timeout
        self._market_factory = market_factory or self._default_factory
        self._markets: dict[str, CcxtMarketData] = {}

    def _default_factory(self, venue: str) -> CcxtMarketData:
        return CcxtMarketData(exchange=venue, quote_ccy=_PEG_QUOTE_CCY, timeout=self._timeout)

    def _market_for(self, venue: str) -> CcxtMarketData:
        if venue not in self._markets:
            self._markets[venue] = self._market_factory(venue)
        return self._markets[venue]

    async def get_peg(
        self, symbols: list[str] | None = None, venue: str | None = None
    ) -> StablecoinPeg:
        venue_name = (venue or self._default_venue).strip().lower()
        requested = [s.strip().upper() for s in (symbols or _DEFAULT_SYMBOLS) if s and s.strip()]
        if not requested:
            requested = list(_DEFAULT_SYMBOLS)
        market = self._market_for(venue_name)
        as_of = datetime.now(UTC)

        reads = await asyncio.gather(
            *(self._read_symbol(market, sym, venue_name) for sym in requested)
        )

        items: list[StablecoinPegItem] = []
        unavailable: list[str] = []
        not_listed: list[str] = []
        status: str | None = None
        for sym, item, item_status, listed in reads:
            if item_status is not None:
                status = status or item_status
                unavailable.append(sym)
            elif not listed:
                not_listed.append(sym)
            elif item is not None:
                items.append(item)

        notes: list[str] = []
        if not_listed:
            notes.append(f"not listed on {venue_name}: {', '.join(not_listed)}")
        if unavailable:
            notes.append(f"unavailable (fetch failed): {', '.join(unavailable)}")
        note = "; ".join(notes) or None

        return StablecoinPeg(items=items, as_of=as_of, source_status=status, note=note)

    async def _read_symbol(
        self, market: CcxtMarketData, symbol: str, venue: str
    ) -> tuple[str, StablecoinPegItem | None, str | None, bool]:
        """Returns ``(symbol, item, status, listed)``. ``status`` set on a fetch failure;
        ``listed`` False when the venue does not carry ``<SYM>/USD``."""
        try:
            quote = await market.get_quote(symbol)
        except SourceUnavailable as exc:
            return symbol, None, exc.status, True
        except Exception as exc:  # noqa: BLE001 — classify: not-listed vs a genuine failure
            if _looks_not_listed(exc):
                return symbol, None, None, False
            return symbol, None, unavailable_status(exc), True

        price = quote.last if quote is not None else None
        if price is None:
            return symbol, None, None, False  # venue does not carry this pair
        deviation_bps = _quantize((price - 1) * _BPS_PER_UNIT, 1)
        depeg = deviation_bps is not None and abs(deviation_bps) > _DEPEG_BPS_THRESHOLD
        item = StablecoinPegItem(
            symbol=symbol,
            venue=venue,
            price=price,
            deviation_bps=deviation_bps,
            depeg=depeg,
        )
        return symbol, item, None, True


def _looks_not_listed(exc: Exception) -> bool:
    """A ccxt ``BadSymbol`` (and kin) means the venue doesn't list the pair — not a throttle."""
    name = type(exc).__name__.lower()
    return "badsymbol" in name or "symbolnotfound" in name
