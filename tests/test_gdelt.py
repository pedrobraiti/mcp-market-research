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
