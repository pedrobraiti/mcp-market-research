from datetime import datetime

from scout.adapters.gdelt import GdeltNewsSearch

_RESPONSE = {
    "articles": [
        {
            "title": "AI data centers strain the power grid",
            "domain": "reuters.com",
            "url": "https://reuters.com/ai-power",
            "seendate": "20260620T143000Z",
            "language": "English",
            "sourcecountry": "United States",
        },
        {"title": "second", "domain": "ft.com", "url": "https://ft.com/x", "seendate": "bad"},
    ]
}


def _source(captured=None):
    async def _fetch(url: str) -> dict:
        if captured is not None:
            captured["url"] = url
        return _RESPONSE

    return GdeltNewsSearch(fetch_json=_fetch)


async def test_search_news_parses_articles():
    captured = {}

    async def _fetch(url: str) -> dict:
        captured["url"] = url
        return _RESPONSE

    source = GdeltNewsSearch(fetch_json=_fetch)
    result = await source.search_news("AI data center power", limit=10, days=7)
    assert result.query == "AI data center power"
    assert "AI%20data%20center%20power" in captured["url"]  # url-encoded query
    assert "timespan=7d" in captured["url"]
    assert len(result.items) == 2
    assert result.items[0].domain == "reuters.com"
    assert result.items[0].published == datetime(2026, 6, 20, 14, 30, 0)
    assert result.items[1].published is None  # bad seendate parsed to None


async def test_search_news_empty_response():
    async def _fetch(url: str) -> dict:
        return {}

    result = await GdeltNewsSearch(fetch_json=_fetch).search_news("nothing")
    assert result.items == []
    assert result.source_status is None  # genuine "no matches", not a fetch failure


class _Resp:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class _FakeHttpError(Exception):
    """Mimics httpx.HTTPStatusError for the retry classifier (carries .response.status_code)."""

    def __init__(self, status_code: int) -> None:
        self.response = _Resp(status_code)
        super().__init__(f"HTTP {status_code}")


async def test_search_news_rate_limited_marks_unavailable():
    calls = {"n": 0}

    async def _fetch(url: str) -> dict:
        calls["n"] += 1
        raise _FakeHttpError(429)

    source = GdeltNewsSearch(fetch_json=_fetch, retry_attempts=3, retry_base_delay=0)
    result = await source.search_news("AI data center power")
    assert calls["n"] == 3  # retried the full budget before giving up
    assert result.items == []
    # A 429 is "couldn't fetch", distinguishable from an empty-but-successful response.
    assert result.source_status == "unavailable: rate_limited"
