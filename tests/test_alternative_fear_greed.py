from datetime import UTC, date, datetime

from scout.adapters.alternative import AlternativeFearGreed


def _ts(year: int, month: int, day: int) -> str:
    return str(int(datetime(year, month, day, tzinfo=UTC).timestamp()))


_RESPONSE = {
    "name": "Fear and Greed Index",
    "data": [
        {"value": "15", "value_classification": "Extreme Fear", "timestamp": _ts(2026, 6, 25)},
        {"value": "22", "value_classification": "Extreme Fear", "timestamp": _ts(2026, 6, 24)},
        {"value": "40", "value_classification": "Fear", "timestamp": _ts(2026, 6, 23)},
    ],
}


def _source(response=_RESPONSE):
    captured = {}

    async def _fetch(url: str) -> dict:
        captured["url"] = url
        return response

    return AlternativeFearGreed(fetch_json=_fetch), captured


async def test_fear_greed_current_and_history():
    source, captured = _source()
    result = await source.get_fear_greed(days=30)
    assert "limit=30" in captured["url"]
    assert result.value == 15
    assert result.classification == "Extreme Fear"
    assert result.observation_date == date(2026, 6, 25)
    assert len(result.history) == 3
    assert result.history[-1].value == 40


async def test_fear_greed_empty_data():
    source, _ = _source(response={"data": []})
    result = await source.get_fear_greed()
    assert result.value is None
    assert result.history == []


async def test_days_clamped_into_url():
    source, captured = _source()
    await source.get_fear_greed(days=0)
    assert "limit=1" in captured["url"]  # clamped to >= 1
