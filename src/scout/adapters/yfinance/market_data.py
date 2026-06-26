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
import time
from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from ...domain.models import (
    AnalystView,
    CompanySnapshot,
    DividendHistory,
    DividendPayment,
    EarningsEvent,
    EarningsInfo,
    Fundamentals,
    NewsItem,
    NewsList,
    Period,
    PriceBar,
    PriceHistory,
    SymbolMatch,
    SymbolSearch,
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


def _default_search(query: str) -> list:
    import yfinance

    return yfinance.Search(query).quotes


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
    def __init__(
        self,
        ticker_factory: Callable[[str], Any] | None = None,
        retry_attempts: int = 3,
        retry_base_delay: float = 0.5,
        search_fn: Callable[[str], list] | None = None,
    ) -> None:
        self._ticker_factory = ticker_factory or _default_ticker_factory
        self._retry_attempts = max(1, retry_attempts)
        self._retry_base_delay = retry_base_delay
        self._search_fn = search_fn or _default_search

    # ---- public async API (the port) -------------------------------------------------

    async def get_snapshot(
        self, symbol: str, as_of: date | None = None
    ) -> CompanySnapshot | None:
        return await asyncio.to_thread(
            self._retrying, self._snapshot_sync, symbol.strip().upper(), as_of
        )

    async def get_fundamentals(
        self, symbol: str, period: Period = Period.ANNUAL, as_of: date | None = None
    ) -> Fundamentals | None:
        return await asyncio.to_thread(
            self._retrying, self._fundamentals_sync, symbol.strip().upper(), period, as_of
        )

    async def get_dividends(
        self, symbol: str, as_of: date | None = None
    ) -> DividendHistory | None:
        return await asyncio.to_thread(
            self._retrying, self._dividends_sync, symbol.strip().upper(), as_of
        )

    async def get_price_history(
        self,
        symbol: str,
        range: str = "6mo",
        interval: str = "1d",
        as_of: date | None = None,
    ) -> PriceHistory | None:
        return await asyncio.to_thread(
            self._retrying, self._price_history_sync, symbol.strip().upper(), range, interval, as_of
        )

    async def get_news(self, symbol: str, limit: int = 10) -> NewsList | None:
        return await asyncio.to_thread(
            self._retrying, self._news_sync, symbol.strip().upper(), max(1, min(limit, 50))
        )

    async def get_earnings(self, symbol: str, as_of: date | None = None) -> EarningsInfo | None:
        return await asyncio.to_thread(
            self._retrying, self._earnings_sync, symbol.strip().upper(), as_of
        )

    async def get_analyst_view(self, symbol: str) -> AnalystView | None:
        return await asyncio.to_thread(self._retrying, self._analyst_sync, symbol.strip().upper())

    async def search_symbols(self, query: str, limit: int = 10) -> SymbolSearch:
        return await asyncio.to_thread(
            self._retrying, self._search_sync, query.strip(), max(1, min(limit, 25))
        )

    def _retrying(self, func: Callable[..., Any], *args: Any) -> Any:
        """Call a blocking fetch, retrying transient failures with exponential backoff.

        yfinance scrapes Yahoo and is rate-limited; a transient error should NOT look like a
        missing symbol. So a network/HTTP failure is retried, and only a persistent failure
        propagates (surfaced as an error envelope) — a genuinely unresolved symbol still
        returns ``None`` without raising.
        """
        last_error: Exception | None = None
        for attempt in range(self._retry_attempts):
            try:
                return func(*args)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < self._retry_attempts - 1 and self._retry_base_delay > 0:
                    time.sleep(self._retry_base_delay * (2**attempt))
        assert last_error is not None
        raise last_error

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
        next_ex = _from_unix(info.get("exDividendDate")) if info else None
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
            next_ex_dividend=next_ex.date() if next_ex else None,
            payments=payments,
            as_of=as_of,
        )

    def _price_history_sync(
        self, symbol: str, range_: str, interval: str, as_of: date | None
    ) -> PriceHistory | None:
        ticker = self._ticker_factory(symbol)
        history = getattr(ticker, "history", None)
        if not callable(history):
            return None
        frame = history(period=range_, interval=interval)
        if frame is None or len(frame) == 0 or "Close" not in getattr(frame, "columns", []):
            return None
        bars: list[PriceBar] = []
        for index_value, row in frame.iterrows():
            bar_date = _to_date(index_value)
            if bar_date is None or (as_of is not None and bar_date > as_of):
                continue
            bars.append(
                PriceBar(
                    date=bar_date,
                    open=_dec(row.get("Open")),
                    high=_dec(row.get("High")),
                    low=_dec(row.get("Low")),
                    close=_dec(row.get("Close")),
                    volume=_volume(row.get("Volume")),
                )
            )
        return PriceHistory(symbol=symbol, interval=interval, bars=bars, as_of=as_of)

    def _news_sync(self, symbol: str, limit: int) -> NewsList:
        ticker = self._ticker_factory(symbol)
        raw = getattr(ticker, "news", None) or []
        items: list[NewsItem] = []
        for entry in raw[:limit]:
            if not isinstance(entry, dict):
                continue
            content = entry.get("content") if isinstance(entry.get("content"), dict) else None
            if content:  # newer yfinance schema
                items.append(
                    NewsItem(
                        title=content.get("title"),
                        summary=content.get("summary") or content.get("description"),
                        url=_nested(content, "canonicalUrl", "url")
                        or _nested(content, "clickThroughUrl", "url"),
                        publisher=_nested(content, "provider", "displayName"),
                        published=_parse_datetime(content.get("pubDate")),
                    )
                )
            else:  # older flat schema
                items.append(
                    NewsItem(
                        title=entry.get("title"),
                        summary=entry.get("summary"),
                        url=entry.get("link"),
                        publisher=entry.get("publisher"),
                        published=_from_unix(entry.get("providerPublishTime")),
                    )
                )
        return NewsList(symbol=symbol, items=items)

    def _earnings_sync(self, symbol: str, as_of: date | None) -> EarningsInfo:
        ticker = self._ticker_factory(symbol)
        getter = getattr(ticker, "get_earnings_dates", None)
        frame = getter(limit=16) if callable(getter) else getattr(ticker, "earnings_dates", None)
        if frame is None or getattr(frame, "empty", True):
            return EarningsInfo(symbol=symbol)
        reference = as_of or date.today()
        events: list[EarningsEvent] = []
        next_date: date | None = None
        for index_value, row in frame.iterrows():
            event_date = _to_date(index_value)
            reported = _dec(row.get("Reported EPS"))
            is_future = reported is None and (event_date is None or event_date >= reference)
            events.append(
                EarningsEvent(
                    event_date=event_date,
                    eps_estimate=_dec(row.get("EPS Estimate")),
                    eps_reported=reported,
                    surprise_percent=_dec(row.get("Surprise(%)")),
                    is_future=is_future,
                )
            )
            if is_future and event_date is not None:
                if next_date is None or event_date < next_date:
                    next_date = event_date
        events.sort(key=lambda e: e.event_date or date.min)
        return EarningsInfo(symbol=symbol, next_earnings_date=next_date, events=events)

    def _search_sync(self, query: str, limit: int) -> SymbolSearch:
        quotes = self._search_fn(query) or []
        matches: list[SymbolMatch] = []
        for quote in quotes[:limit]:
            if not isinstance(quote, dict):
                continue
            symbol = quote.get("symbol")
            if not symbol:
                continue
            matches.append(
                SymbolMatch(
                    symbol=symbol,
                    name=quote.get("shortname") or quote.get("longname"),
                    exchange=quote.get("exchange") or quote.get("exchDisp"),
                    type=quote.get("quoteType") or quote.get("typeDisp"),
                )
            )
        return SymbolSearch(query=query, matches=matches)

    def _analyst_sync(self, symbol: str) -> AnalystView | None:
        info = _info(self._ticker_factory(symbol))
        if not info:
            return None
        return AnalystView(
            symbol=symbol,
            recommendation_key=info.get("recommendationKey"),
            recommendation_mean=_dec(info.get("recommendationMean")),
            number_of_analysts=_int(info.get("numberOfAnalystOpinions")),
            current_price=_dec(info.get("currentPrice") or info.get("regularMarketPrice")),
            target_mean=_dec(info.get("targetMeanPrice")),
            target_median=_dec(info.get("targetMedianPrice")),
            target_high=_dec(info.get("targetHighPrice")),
            target_low=_dec(info.get("targetLowPrice")),
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
    # Deliberately does NOT swallow exceptions: a transient/HTTP error must propagate so the
    # retry wrapper can back off (instead of masquerading as an unresolved symbol). A symbol
    # that simply has no data returns a non-dict/empty payload, which becomes {} → unresolved.
    info = ticker.info
    return info if isinstance(info, dict) else {}


def _currency(info: dict) -> str:
    return info.get("currency") or "USD"


def _volume(value: Any) -> int | None:
    decimal_value = _dec(value)
    return int(decimal_value) if decimal_value is not None else None


def _int(value: Any) -> int | None:
    decimal_value = _dec(value)
    return int(decimal_value) if decimal_value is not None else None


def _nested(data: dict, *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current if isinstance(current, str) else None


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _from_unix(value: Any) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(value), tz=UTC) if value else None
    except (ValueError, TypeError, OSError):
        return None


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
