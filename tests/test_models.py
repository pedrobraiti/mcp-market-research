from datetime import date
from decimal import Decimal

from scout.domain.models import (
    CompanySnapshot,
    DividendHistory,
    DividendPayment,
    Fundamentals,
    Period,
)


def test_snapshot_serializes_decimals_as_strings():
    snapshot = CompanySnapshot(symbol="AAPL", price=Decimal("230.0"), change=Decimal("2.0"))
    dumped = snapshot.model_dump(mode="json")
    assert dumped["symbol"] == "AAPL"
    assert dumped["price"] == "230.0"
    assert dumped["as_of"] is None


def test_fundamentals_holds_period_and_margins():
    fundamentals = Fundamentals(
        symbol="AAPL", period=Period.ANNUAL, revenue=Decimal("100"), net_income=Decimal("25")
    )
    assert fundamentals.period == Period.ANNUAL
    assert fundamentals.model_dump(mode="json")["revenue"] == "100"


def test_dividend_history_defaults_to_empty_payments():
    history = DividendHistory(symbol="KO")
    assert history.payments == []
    assert history.had_cut is None


def test_dividend_payment_keeps_ex_date():
    payment = DividendPayment(ex_date=date(2024, 8, 12), amount=Decimal("0.25"))
    assert payment.ex_date.year == 2024
