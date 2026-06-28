from decimal import Decimal

from scout.adapters.derivatives import DerivativesAggregator


async def _fetch(url: str):
    if "fapi.binance.com" in url and "premiumIndex" in url:
        return {
            "lastFundingRate": "0.00004111",
            "markPrice": "60000.0",
            "nextFundingTime": 1782000000000,
        }
    if "fapi.binance.com" in url and "openInterest" in url:
        return {"openInterest": "10000.0"}
    if "bybit.com" in url:
        return {
            "result": {
                "list": [
                    {
                        "fundingRate": "0.00005",
                        "nextFundingTime": "1782000000000",
                        "markPrice": "60010.0",
                        "openInterest": "8000",
                        "openInterestValue": "480080000",
                    }
                ]
            }
        }
    if "okx.com" in url and "funding-rate" in url:
        return {"data": [{"fundingRate": "0.00003", "nextFundingTime": "1782000000000"}]}
    if "okx.com" in url and "open-interest" in url:
        return {"data": [{"oiCcy": "5000", "oiUsd": "300000000"}]}
    raise AssertionError(url)


async def test_aggregates_three_venues():
    result = await DerivativesAggregator(fetch_json=_fetch).get_derivatives("BTC")
    assert result.base == "BTC"
    venues = {v.exchange: v for v in result.venues}
    assert set(venues) == {"binance", "bybit", "okx"}
    assert venues["binance"].funding_rate == Decimal("0.00004111")
    # binance OI value = 10000 * 60000
    assert venues["binance"].open_interest_value == Decimal("600000000.0")
    assert venues["bybit"].open_interest_value == Decimal("480080000")
    assert venues["okx"].open_interest_value == Decimal("300000000")


async def test_derived_funding_annualized_and_cross_venue():
    result = await DerivativesAggregator(fetch_json=_fetch).get_derivatives("BTC")
    venues = {v.exchange: v for v in result.venues}
    # Per-venue annualization at the 8h default: 0.00004111 × 3 × 365.
    assert venues["binance"].funding_rate_annualized == Decimal("0.045015")
    # OI-weighted consensus sits between the venues' funding rates.
    assert result.funding_oi_weighted is not None
    assert Decimal("0.00003") < result.funding_oi_weighted < Decimal("0.00005")
    assert result.funding_annualized_oi_weighted is not None
    # Dispersion = max − min funding = 0.00005 − 0.00003.
    assert result.funding_dispersion == Decimal("0.00002000")
    # Total OI in USD = 600,000,000 + 480,080,000 + 300,000,000.
    assert result.total_open_interest_value == Decimal("1380080000.00")
    assert result.note is not None and "8h" in result.note
    assert result.partial is False  # all three venues returned


async def test_partial_failure_drops_only_that_venue():
    async def flaky(url: str):
        if "bybit.com" in url:
            raise RuntimeError("bybit down")
        return await _fetch(url)

    result = await DerivativesAggregator(fetch_json=flaky).get_derivatives("BTC")
    exchanges = {v.exchange for v in result.venues}
    assert exchanges == {"binance", "okx"}
    assert result.partial is True  # a venue was dropped → aggregates are thinner


async def test_all_fail_returns_note():
    async def dead(url: str):
        raise RuntimeError("network down")

    result = await DerivativesAggregator(fetch_json=dead).get_derivatives("BTC")
    assert result.venues == []
    assert result.note is not None
