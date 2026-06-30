"""Coinbase (US-spot, USD) vs Binance (offshore, USDT) price premium — keyless, CCXT-derived.

The premium is the gap between the US-spot price (Coinbase, USD) and the offshore price (Binance,
USDT). Positive = aggressive US buying (the ETF/institutional bid tell); negative = US selling
pressure. It is paywalled elsewhere (CryptoQuant); here it is pure arithmetic on two spot prices
Scout can already fetch.

Two venues, so two ``CcxtMarketData`` instances are composed — one per exchange — each keeping its
own shared, rate-limited exchange (see ``market_data._shared_exchange``). They are injected so the
unit tests run fully offline, with no network and no ccxt import.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from ...analytics import zscore_of_last
from ...domain.models import CoinbasePremium, PremiumPoint
from ..retry import SourceUnavailable, unavailable_status
from .market_data import CcxtMarketData

_MIN_DAYS = 1
_MAX_DAYS = 90
_MIN_PREMIUM_POINTS = 8  # below this the premium z-score is too noisy to report


def _quantize(value: Decimal | None, places: int) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)


def _premium_pct(us_price: Decimal, offshore_price: Decimal) -> Decimal | None:
    if offshore_price == 0:
        return None
    return _quantize((us_price - offshore_price) / offshore_price * 100, 4)


@dataclass
class _VenueRead:
    """One venue's read: a price (and/or a daily close series), or a failure flag."""

    price: Decimal | None = None
    closes_by_date: dict | None = None  # date -> close Decimal
    status: str | None = None  # 'unavailable: <reason>' when a throttle/timeout/error hit
    not_listed: bool = False  # the venue simply does not list this pair (distinct from a throttle)


class CcxtPremium:
    def __init__(
        self,
        us_market: CcxtMarketData,
        offshore_market: CcxtMarketData,
        us_venue: str = "coinbase",
        offshore_venue: str = "binance",
    ) -> None:
        self._us_market = us_market
        self._offshore_market = offshore_market
        self._us_venue = us_venue
        self._offshore_venue = offshore_venue

    async def get_premium(self, symbol: str = "BTC", days: int = 30) -> CoinbasePremium:
        base = symbol.strip().upper().split("/")[0]
        if not base:
            raise ValueError(f"Could not parse a crypto base asset from {symbol!r}.")
        bounded_days = max(_MIN_DAYS, min(int(days), _MAX_DAYS))
        as_of = datetime.now(UTC)

        us_read, offshore_read = await asyncio.gather(
            self._read_venue(self._us_market, base, bounded_days),
            self._read_venue(self._offshore_market, base, bounded_days),
        )

        # A throttle/timeout/error on either leg means the premium can't be computed honestly from
        # one price — surface it as unavailable rather than a fake number (ADR-012).
        status = us_read.status or offshore_read.status
        if status is not None:
            return CoinbasePremium(
                symbol=base,
                coinbase_price=us_read.price,
                binance_price=offshore_read.price,
                as_of=as_of,
                source_status=status,
                note="Premium needs both venues; one leg was unavailable.",
            )

        # A venue that simply does not list the pair is a real, non-throttle 'not here' — empty
        # with a note, distinct from an unavailable status.
        not_listed = [
            venue
            for venue, read in (
                (self._us_venue, us_read),
                (self._offshore_venue, offshore_read),
            )
            if read.not_listed
        ]
        if not_listed:
            return CoinbasePremium(
                symbol=base,
                coinbase_price=us_read.price,
                binance_price=offshore_read.price,
                as_of=as_of,
                note=f"{base} is not listed on: {', '.join(not_listed)}.",
            )

        premium_pct = (
            _premium_pct(us_read.price, offshore_read.price)
            if us_read.price is not None and offshore_read.price is not None
            else None
        )
        history = self._build_history(us_read.closes_by_date, offshore_read.closes_by_date)
        series = [float(p.premium_pct) for p in history if p.premium_pct is not None]
        zscore = (
            _quantize(_to_dec(zscore_of_last(series)), 4)
            if len(series) >= _MIN_PREMIUM_POINTS
            else None
        )
        return CoinbasePremium(
            symbol=base,
            coinbase_price=us_read.price,
            binance_price=offshore_read.price,
            premium_pct=premium_pct,
            premium_zscore=zscore,
            history=history,
            as_of=as_of,
            note=(
                f"premium = ({self._us_venue} US-spot − {self._offshore_venue} offshore) / "
                "offshore × 100; a positioning tell, not a price."
            ),
        )

    @staticmethod
    def _build_history(
        us_closes: dict | None, offshore_closes: dict | None
    ) -> list[PremiumPoint]:
        if not us_closes or not offshore_closes:
            return []
        common = sorted(set(us_closes) & set(offshore_closes))
        points: list[PremiumPoint] = []
        for day in common:
            premium = _premium_pct(us_closes[day], offshore_closes[day])
            points.append(PremiumPoint(date=day, premium_pct=premium))
        return points

    async def _read_venue(self, market: CcxtMarketData, base: str, days: int) -> _VenueRead:
        try:
            quote, history = await asyncio.gather(
                market.get_quote(base),
                market.get_price_history(base, "1d", days),
            )
        except SourceUnavailable as exc:
            return _VenueRead(status=exc.status)
        except Exception as exc:  # noqa: BLE001 — classify: not-listed vs a genuine failure
            if _looks_not_listed(exc):
                return _VenueRead(not_listed=True)
            return _VenueRead(status=unavailable_status(exc))

        price = quote.last if quote is not None else None
        closes_by_date: dict = {}
        if history is not None:
            for bar in history.bars:
                if bar.close is not None:
                    closes_by_date[bar.timestamp.date()] = bar.close
        # No live price AND no candles → the venue does not carry this pair.
        if price is None and not closes_by_date:
            return _VenueRead(not_listed=True)
        return _VenueRead(price=price, closes_by_date=closes_by_date)


def _to_dec(value: float | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _looks_not_listed(exc: Exception) -> bool:
    """A ccxt ``BadSymbol`` (and kin) means the venue doesn't list the pair — not a throttle."""
    name = type(exc).__name__.lower()
    return "badsymbol" in name or "symbolnotfound" in name
