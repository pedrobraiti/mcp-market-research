from datetime import date
from decimal import Decimal

from scout.adapters.fred import FredMacro

# Per-series canned CSVs; the dot marks a missing observation (FRED's convention).
_CSV = {
    "FEDFUNDS": "DATE,FEDFUNDS\n2026-04-01,3.62\n2026-05-01,3.63\n",
    "DGS10": "DATE,DGS10\n2026-06-23,4.45\n2026-06-24,.\n2026-06-25,4.47\n",
    "DGS2": "DATE,DGS2\n2026-06-25,4.10\n",
    "T10Y2Y": "DATE,T10Y2Y\n2026-06-25,0.37\n",
    "UNRATE": "DATE,UNRATE\n2026-05-01,4.3\n",
    "CPIAUCSL": "DATE,CPIAUCSL\n2026-05-01,322.1\n",
    "VIXCLS": "DATE,VIXCLS\n2026-06-25,18.4\n",
}


def _fetch_factory(store=_CSV):
    async def _fetch(url: str) -> str:
        series = url.split("id=")[-1]
        return store[series]

    return _fetch


async def test_returns_all_series_latest():
    snapshot = await FredMacro(fetch_csv=_fetch_factory()).get_macro_context()
    by_id = {i.series_id: i for i in snapshot.indicators}
    assert len(snapshot.indicators) == 7
    assert by_id["FEDFUNDS"].value == Decimal("3.63")
    # The latest DGS10 row is valid; the dot row before it is skipped.
    assert by_id["DGS10"].value == Decimal("4.47")
    assert by_id["DGS10"].observation_date == date(2026, 6, 25)


async def test_as_of_picks_earlier_observation():
    snapshot = await FredMacro(fetch_csv=_fetch_factory()).get_macro_context(
        as_of=date(2026, 6, 23)
    )
    by_id = {i.series_id: i for i in snapshot.indicators}
    assert by_id["DGS10"].value == Decimal("4.45")
    assert by_id["DGS10"].observation_date == date(2026, 6, 23)


async def test_partial_failure_drops_only_that_series():
    async def flaky_fetch(url: str) -> str:
        if "VIXCLS" in url:
            raise RuntimeError("series fetch failed")
        return _CSV[url.split("id=")[-1]]

    snapshot = await FredMacro(fetch_csv=flaky_fetch).get_macro_context()
    ids = {i.series_id for i in snapshot.indicators}
    assert "VIXCLS" not in ids
    assert "FEDFUNDS" in ids
    assert len(snapshot.indicators) == 6
