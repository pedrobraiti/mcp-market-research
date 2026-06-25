from datetime import date

from scout.adapters.sec import SecEdgarFilings

_TICKERS = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
}

_SUBMISSIONS = {
    "name": "Apple Inc.",
    "filings": {
        "recent": {
            "form": ["10-K", "8-K", "10-Q", "4"],
            "filingDate": ["2024-11-01", "2024-10-15", "2024-08-02", "2024-07-20"],
            "reportDate": ["2024-09-28", "", "2024-06-29", ""],
            "accessionNumber": [
                "0000320193-24-000123",
                "0000320193-24-000110",
                "0000320193-24-000081",
                "0000320193-24-000070",
            ],
            "primaryDocument": ["aapl-20240928.htm", "ex.htm", "aapl-20240629.htm", "form4.xml"],
            "primaryDocDescription": ["10-K", "8-K", "10-Q", "FORM 4"],
        }
    },
}


def _fetch_factory():
    async def _fetch(url: str) -> dict:
        if "company_tickers" in url:
            return _TICKERS
        return _SUBMISSIONS

    return _fetch


def _source():
    return SecEdgarFilings("Test Agent test@example.com", fetch_json=_fetch_factory())


async def test_resolves_cik_and_returns_filings():
    result = await _source().get_filings("aapl")
    assert result is not None
    assert result.cik == "0000320193"
    assert result.name == "Apple Inc."
    assert len(result.filings) == 4
    first = result.filings[0]
    assert first.form == "10-K"
    assert first.filing_date == date(2024, 11, 1)
    assert first.report_date == date(2024, 9, 28)
    # URL drops the dashes in the accession and the leading zeros in the CIK path.
    assert first.url == (
        "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm"
    )


async def test_filters_by_form_type():
    result = await _source().get_filings("AAPL", form_type="10-q")
    assert result is not None
    assert len(result.filings) == 1
    assert result.filings[0].form == "10-Q"


async def test_filters_by_as_of():
    result = await _source().get_filings("AAPL", as_of=date(2024, 9, 1))
    assert result is not None
    # Only the 2024-08-02 (10-Q) and 2024-07-20 (4) filings are on/before 2024-09-01.
    assert [f.form for f in result.filings] == ["10-Q", "4"]


async def test_limit_caps_results():
    result = await _source().get_filings("AAPL", limit=2)
    assert result is not None
    assert len(result.filings) == 2


async def test_unresolved_symbol_returns_none():
    assert await _source().get_filings("NOPE") is None
