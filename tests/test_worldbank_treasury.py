from datetime import date
from decimal import Decimal

from scout.adapters.treasury import TreasuryFiscal
from scout.adapters.worldbank import WorldBankMacro

# ---- World Bank ----------------------------------------------------------------------


def _wb_response(code, value, year):
    return [
        {"page": 1, "pages": 1},
        [
            {
                "indicator": {"id": code, "value": f"name-{code}"},
                "countryiso3code": "USA",
                "date": year,
                "value": value,
            }
        ],
    ]


def _wb_source():
    async def _fetch(url: str):
        # Newest-first list with a null most-recent year to test skipping.
        if "NY.GDP.MKTP.KD.ZG" in url:
            return [
                {"page": 1},
                [
                    {"indicator": {"value": "GDP growth"}, "date": "2025", "value": None},
                    {"indicator": {"value": "GDP growth"}, "countryiso3code": "USA",
                     "date": "2024", "value": 2.8},
                ],
            ]
        return _wb_response("X", 10, "2024")

    return WorldBankMacro(fetch_json=_fetch)


async def test_world_bank_picks_latest_non_null():
    data = await _wb_source().get_indicators("usa", codes=["NY.GDP.MKTP.KD.ZG"])
    assert data.country == "USA"
    assert len(data.indicators) == 1
    indicator = data.indicators[0]
    assert indicator.value == Decimal("2.8")
    assert indicator.year == 2024  # skipped the null 2025 observation


# ---- Treasury ------------------------------------------------------------------------


def _treasury_source():
    async def _fetch(url: str) -> dict:
        if "debt_to_penny" in url:
            debt = {"record_date": "2026-06-24", "tot_pub_debt_out_amt": "36000000000000.00"}
            return {"data": [debt]}
        return {
            "data": [
                {"record_date": "2026-05-31", "security_desc": "Treasury Bills",
                 "avg_interest_rate_amt": "4.5"},
                {"record_date": "2026-05-31", "security_desc": "Treasury Notes",
                 "avg_interest_rate_amt": "3.1"},
                {"record_date": "2026-04-30", "security_desc": "Treasury Bills",
                 "avg_interest_rate_amt": "4.6"},
            ]
        }

    return TreasuryFiscal(fetch_json=_fetch)


async def test_treasury_debt_and_latest_rates():
    data = await _treasury_source().get_data()
    by_name = {f.name: f for f in data.figures}
    assert by_name["Total public debt outstanding"].value == Decimal("36000000000000.00")
    assert by_name["Total public debt outstanding"].record_date == date(2026, 6, 24)
    # Only the latest record_date (2026-05-31) rates are included → 2 figures, not the April one.
    rate_figures = [f for f in data.figures if f.unit == "%"]
    assert len(rate_figures) == 2
    assert by_name["Avg interest rate — Treasury Bills"].value == Decimal("4.5")
