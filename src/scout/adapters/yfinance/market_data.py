"""yfinance implementation of ``MarketDataSource``.

yfinance is synchronous and network-bound, so every blocking call is pushed to a thread
(``asyncio.to_thread``) — this keeps the port async and lets a future ``company_dossier``
fan several of these out concurrently with ``asyncio.gather``.

The concrete ``yfinance.Ticker`` is injected via ``ticker_factory`` (imported lazily, only
when the default factory is actually used) so the unit tests run fully offline with a fake.
"""

from __future__ import annotations

import asyncio
import math
from collections.abc import Callable
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from ...domain.models import (
    CompanySnapshot,
    DividendHistory,
    DividendPayment,
    Fundamentals,
    Period,
)

# A revenue/gross-profit/etc. line item is looked up by trying several label spellings,
# since yfinance's row labels drift between versions and filings.
_REVENUE = ("Total Revenue", "Operating Revenue", "Revenue")
_GROSS_PROFIT = ("Gross Profit",)
_OPERATING_INCOME = ("Operating Income", "Total Operating Income As Reported")
_NET_INCOME = (
    "Net Income",
    "Net Income Common Stockholders",
    "Net Income From Continuing Operation Net Minority Interest",
)
_TOTAL_DEBT = ("Total Debt",)
_TOTAL_CASH = (
    "Cash And Cash Equivalents",
    "Cash Cash Equivalents And Short Term Investments",
    "Cash And Cash Equivalents And Short Term Investments",
)
_FREE_CASH_FLOW = ("Free Cash Flow",)


def _default_ticker_factory(symbol: str) -> Any:
    import yfinance  # imported lazily so tests never need the package or the network

    return yfinance.Ticker(symbol)


def _dec(value: Any) -> Decimal | None:
    """Coerce a yfinance/pandas value to ``Decimal``; NaN/None/garbage become ``None``."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return None if result.is_nan() else result


def _to_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    # pandas Timestamp and most date-likes expose .date(); fall back to parsing the string.
    to_date = getattr(value, "date", None)
    if callable(to_date):
        try:
            return to_date()
        except Exception:  # noqa: BLE001
            pass
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except ValueError:
        return None


def _quantize(value: Decimal | None, places: int) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)


def _ratio(numerator: Decimal | None, denominator: Decimal | None, places: int) -> Decimal | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return _quantize(numerator / denominator, places)


class YFinanceMarketData:
    def __init__(self, ticker_factory: Callable[[str], Any] | None = None) -> None:
        self._ticker_factory = ticker_factory or _default_ticker_factory

    # ---- public async API (the port) -------------------------------------------------

    async def get_snapshot(
        self, symbol: str, as_of: date | None = None
    ) -> CompanySnapshot | None:
        return await asyncio.to_thread(self._snapshot_sync, symbol.strip().upper(), as_of)

    async def get_fundamentals(
        self, symbol: str, period: Period = Period.ANNUAL, as_of: date | None = None
    ) -> Fundamentals | None:
        return await asyncio.to_thread(
            self._fundamentals_sync, symbol.strip().upper(), period, as_of
        )

    async def get_dividends(
        self, symbol: str, as_of: date | None = None
    ) -> DividendHistory | None:
        return await asyncio.to_thread(self._dividends_sync, symbol.strip().upper(), as_of)

    # ---- blocking implementations ----------------------------------------------------

    def _snapshot_sync(self, symbol: str, as_of: date | None) -> CompanySnapshot | None:
        ticker = self._ticker_factory(symbol)
        info = _info(ticker)
        if as_of is not None:
            price, previous_close = self._history_closes(ticker, as_of)
            if price is None and not info:
                return None
            return CompanySnapshot(
                symbol=symbol,
                name=info.get("longName") or info.get("shortName"),
                currency=info.get("currency") or "USD",
                price=price,
                previous_close=previous_close,
                change=_subtract(price, previous_close),
                change_percent=_pct_change(price, previous_close),
                sector=info.get("sector"),
                industry=info.get("industry"),
                as_of=as_of,
            )

        if not info:
            return None
        price = _dec(info.get("currentPrice") or info.get("regularMarketPrice"))
        previous_close = _dec(info.get("previousClose"))
        return CompanySnapshot(
            symbol=symbol,
            name=info.get("longName") or info.get("shortName"),
            currency=info.get("currency") or "USD",
            price=price,
            previous_close=previous_close,
            change=_subtract(price, previous_close),
            change_percent=_pct_change(price, previous_close),
            market_cap=_dec(info.get("marketCap")),
            pe_ratio=_dec(info.get("trailingPE")),
            forward_pe=_dec(info.get("forwardPE")),
            dividend_yield=_dec(info.get("dividendYield")),
            fifty_two_week_high=_dec(info.get("fiftyTwoWeekHigh")),
            fifty_two_week_low=_dec(info.get("fiftyTwoWeekLow")),
            sector=info.get("sector"),
            industry=info.get("industry"),
            as_of=None,
        )

    def _fundamentals_sync(
        self, symbol: str, period: Period, as_of: date | None
    ) -> Fundamentals | None:
        ticker = self._ticker_factory(symbol)
        quarterly = period is Period.QUARTERLY
        income = _statement(ticker, "quarterly_income_stmt" if quarterly else "income_stmt")
        balance = _statement(ticker, "quarterly_balance_sheet" if quarterly else "balance_sheet")
        cash = _statement(ticker, "quarterly_cashflow" if quarterly else "cashflow")

        column = _pick_column(income, as_of)
        if column is None:
            return None

        revenue = _row(income, column, *_REVENUE)
        gross_profit = _row(income, column, *_GROSS_PROFIT)
        operating_income = _row(income, column, *_OPERATING_INCOME)
        net_income = _row(income, column, *_NET_INCOME)
        balance_col = _pick_column(balance, as_of)
        cash_col = _pick_column(cash, as_of)
        return Fundamentals(
            symbol=symbol,
            period=period,
            fiscal_period_end=_to_date(column),
            revenue=revenue,
            gross_profit=gross_profit,
            operating_income=operating_income,
            net_income=net_income,
            gross_margin=_ratio(gross_profit, revenue, 6),
            operating_margin=_ratio(operating_income, revenue, 6),
            net_margin=_ratio(net_income, revenue, 6),
            total_debt=_row(balance, balance_col, *_TOTAL_DEBT) if balance_col else None,
            total_cash=_row(balance, balance_col, *_TOTAL_CASH) if balance_col else None,
            free_cash_flow=_row(cash, cash_col, *_FREE_CASH_FLOW) if cash_col else None,
            as_of=as_of,
        )

    def _dividends_sync(self, symbol: str, as_of: date | None) -> DividendHistory | None:
        ticker = self._ticker_factory(symbol)
        series = getattr(ticker, "dividends", None)
        if series is None or len(series) == 0:
            # A valid symbol that simply pays no dividend → an empty, honest history.
            info = _info(ticker)
            if not info and not self._history_closes(ticker, as_of or date.today())[0]:
                return None
            return DividendHistory(symbol=symbol, currency=_currency(info), as_of=as_of)

        payments: list[DividendPayment] = []
        for index_value, amount in series.items():
            ex_date = _to_date(index_value)
            value = _dec(amount)
            if ex_date is None or value is None:
                continue
            if as_of is not None and ex_date > as_of:
                continue
            payments.append(DividendPayment(ex_date=ex_date, amount=value))
        payments.sort(key=lambda p: p.ex_date)

        info = _info(ticker)
        reference = as_of or date.today()
        trailing_12m = _trailing_sum(payments, reference)
        price = _dec(info.get("currentPrice") or info.get("regularMarketPrice")) if info else None
        annual = _annual_totals(payments)
        return DividendHistory(
            symbol=symbol,
            currency=_currency(info),
            trailing_12m=trailing_12m,
            trailing_yield=_ratio(trailing_12m, price, 6),
            growth_streak_years=_growth_streak(annual, reference.year),
            had_cut=_had_cut(annual),
            payments=payments,
            as_of=as_of,
        )

    def _history_closes(self, ticker: Any, as_of: date) -> tuple[Decimal | None, Decimal | None]:
        """Return (close at/just before as_of, the close before that), best-effort."""
        history = getattr(ticker, "history", None)
        if not callable(history):
            return None, None
        try:
            frame = history(start=str(as_of.replace(day=1)), end=str(as_of))
        except Exception:  # noqa: BLE001
            return None, None
        if frame is None or len(frame) == 0 or "Close" not in getattr(frame, "columns", []):
            return None, None
        closes = [_dec(v) for v in frame["Close"].tolist()]
        closes = [c for c in closes if c is not None]
        if not closes:
            return None, None
        price = closes[-1]
        previous = closes[-2] if len(closes) >= 2 else None
        return price, previous


# ---- module-level helpers (pure, easy to reason about) -------------------------------


def _info(ticker: Any) -> dict:
    try:
        info = ticker.info
    except Exception:  # noqa: BLE001
        return {}
    return info if isinstance(info, dict) else {}


def _currency(info: dict) -> str:
    return info.get("currency") or "USD"


def _subtract(a: Decimal | None, b: Decimal | None) -> Decimal | None:
    return a - b if a is not None and b is not None else None


def _pct_change(price: Decimal | None, previous: Decimal | None) -> Decimal | None:
    if price is None or previous is None or previous == 0:
        return None
    return _quantize((price - previous) / previous * Decimal(100), 4)


def _statement(ticker: Any, attr: str) -> Any:
    return getattr(ticker, attr, None)


def _pick_column(statement: Any, as_of: date | None) -> Any:
    """Pick the statement column (period end) that is latest, or latest at/before as_of."""
    if statement is None or getattr(statement, "empty", True):
        return None
    columns = list(statement.columns)
    if not columns:
        return None
    if as_of is None:
        return max(columns, key=lambda c: _to_date(c) or date.min)
    eligible = [c for c in columns if (_to_date(c) or date.max) <= as_of]
    if not eligible:
        return None
    return max(eligible, key=lambda c: _to_date(c) or date.min)


def _row(statement: Any, column: Any, *labels: str) -> Decimal | None:
    if statement is None or column is None:
        return None
    index = getattr(statement, "index", [])
    for label in labels:
        if label in index:
            try:
                return _dec(statement.at[label, column])
            except (KeyError, IndexError):
                continue
    return None


def _trailing_sum(payments: list[DividendPayment], reference: date) -> Decimal | None:
    window_start = reference.replace(year=reference.year - 1)
    total = sum(
        (p.amount for p in payments if window_start < p.ex_date <= reference), Decimal(0)
    )
    return total if total > 0 else None


def _annual_totals(payments: list[DividendPayment]) -> dict[int, Decimal]:
    totals: dict[int, Decimal] = {}
    for payment in payments:
        totals[payment.ex_date.year] = totals.get(payment.ex_date.year, Decimal(0)) + payment.amount
    return totals


def _had_cut(annual: dict[int, Decimal]) -> bool | None:
    """True if any ADJACENT calendar year cut the dividend.

    Only consecutive years are compared — a multi-year gap (e.g. a suspension with no data,
    like Apple's 1996–2012) is not treated as a cut, because absent data and a true cut are
    indistinguishable here. We report only what we can stand behind.
    """
    if len(annual) < 2:
        return None
    years = sorted(annual)
    return any(
        annual[y] < annual[prev]
        for prev, y in zip(years, years[1:], strict=False)
        if y - prev == 1
    )


def _growth_streak(annual: dict[int, Decimal], current_year: int) -> int | None:
    """Consecutive most-recent COMPLETE calendar years of non-decreasing annual dividend.

    Counts only truly adjacent years: a gap in the history ends the streak rather than being
    jumped over (which would inflate the count across a dividend suspension).
    """
    complete = {y: total for y, total in annual.items() if y < current_year}
    if len(complete) < 2:
        return None
    years = sorted(complete, reverse=True)
    streak = 0
    for newer, older in zip(years, years[1:], strict=False):
        if newer - older == 1 and complete[newer] >= complete[older]:
            streak += 1
        else:
            break
    return streak
