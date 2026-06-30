from decimal import Decimal

from scout.adapters.cftc import CftcPositioning


def _row(name, date_str, nc_long, nc_short, oi, *, comm_long=0, comm_short=0,
         chg_long=0, chg_short=0, traders_long=10, traders_short=8, code="088691"):
    return {
        "market_and_exchange_names": name,
        "commodity_name": "GOLD",
        "contract_market_name": "GOLD",
        "cftc_contract_market_code": code,
        "report_date_as_yyyy_mm_dd": date_str,
        "noncomm_positions_long_all": str(nc_long),
        "noncomm_positions_short_all": str(nc_short),
        "comm_positions_long_all": str(comm_long),
        "comm_positions_short_all": str(comm_short),
        "open_interest_all": str(oi),
        "change_in_noncomm_long_all": str(chg_long),
        "change_in_noncomm_short_all": str(chg_short),
        "traders_noncomm_long_all": str(traders_long),
        "traders_noncomm_short_all": str(traders_short),
    }


def _gold_weeks(count):
    """`count` weekly GOLD rows, newest-first (as Socrata returns them)."""
    rows = []
    for i in range(count):
        month = 6 - (i // 4)
        day = 23 - (i % 4) * 7
        rows.append(
            _row(
                "GOLD - COMMODITY EXCHANGE INC.",
                f"2026-{month:02d}-{day:02d}T00:00:00.000",
                nc_long=200_000 + i * 1000,
                nc_short=35_000,
                oi=497_446,
                chg_long=1500,
                chg_short=500,
            )
        )
    return rows


def _source(rows):
    async def _fetch(url: str):
        return rows

    return CftcPositioning(fetch_json=_fetch, retry_base_delay=0.0)


async def test_latest_net_pct_oi_and_wow_change():
    rows = _gold_weeks(12)
    report = await _source(rows).get_positioning("GOLD", weeks=12)
    assert report.market == "GOLD"
    assert report.market_name == "GOLD - COMMODITY EXCHANGE INC."
    # Latest row is the newest (first in the list): nc_long=200000, nc_short=35000.
    assert report.noncomm_long == Decimal("200000")
    assert report.noncomm_short == Decimal("35000")
    assert report.noncomm_net == Decimal("165000")
    # 165000 / 497446 * 100 ≈ 33.1694
    assert report.noncomm_net_pct_oi == Decimal("33.1694")
    # WoW = change_long − change_short = 1500 − 500 = 1000
    assert report.noncomm_net_change == Decimal("1000")
    assert report.traders_noncomm_long == 10
    assert report.as_of is not None and report.as_of.year == 2026
    assert len(report.history) == 12
    # History is oldest → newest.
    assert report.history[0].report_date < report.history[-1].report_date


async def test_multi_market_focuses_highest_open_interest_and_notes_others():
    rows = [
        # MICRO GOLD: matches "GOLD" but tiny open interest → must NOT be primary.
        _row("MICRO GOLD - COMMODITY EXCHANGE INC.", "2026-06-23T00:00:00.000",
             nc_long=5_000, nc_short=2_000, oi=20_000, code="4GC"),
        # GOLD: the headline market, far larger OI → the primary series.
        _row("GOLD - COMMODITY EXCHANGE INC.", "2026-06-23T00:00:00.000",
             nc_long=208_278, nc_short=35_394, oi=497_446),
    ]
    report = await _source(rows).get_positioning("GOLD", weeks=4)
    assert report.market_name == "GOLD - COMMODITY EXCHANGE INC."
    assert report.noncomm_net == Decimal("172884")  # 208278 − 35394
    assert report.matched_markets == ["MICRO GOLD - COMMODITY EXCHANGE INC."]
    assert "MICRO GOLD" in (report.note or "")


async def test_zscore_null_under_eight_weeks():
    report = await _source(_gold_weeks(5)).get_positioning("GOLD", weeks=12)
    assert len(report.history) == 5
    assert report.noncomm_net_zscore is None  # < 8 weekly points → too noisy to report


async def test_zscore_present_with_enough_weeks():
    report = await _source(_gold_weeks(12)).get_positioning("GOLD", weeks=12)
    assert report.noncomm_net_zscore is not None


async def test_no_market_match_returns_note_not_failure():
    report = await _source([]).get_positioning("NONSENSE", weeks=12)
    assert report.source_status is None  # NOT a fetch failure
    assert report.market_name is None
    assert report.history == []
    assert report.note is not None and "No CFTC COT market" in report.note


async def test_unavailable_path_surfaces_source_status():
    class _Resp:
        status_code = 429

    class _RateLimited(Exception):
        def __init__(self):
            self.response = _Resp()
            super().__init__("HTTP 429")

    async def _fetch(url: str):
        raise _RateLimited()

    report = await CftcPositioning(
        fetch_json=_fetch, retry_attempts=2, retry_base_delay=0.0
    ).get_positioning("GOLD", weeks=12)
    assert report.source_status is not None
    assert report.source_status.startswith("unavailable")
    assert report.history == []
    assert report.note is None  # distinct from the "no match" path
