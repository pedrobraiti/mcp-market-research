from scout.adapters.wikimedia import WikimediaPageviews


async def test_pageviews_sums_and_parses():
    captured = {}

    async def _fetch(url: str) -> dict:
        captured["url"] = url
        return {
            "items": [
                {"timestamp": "2026060100", "views": 1000},
                {"timestamp": "2026060200", "views": 1500},
                {"timestamp": "badtimestamp", "views": 9},  # skipped
            ]
        }

    source = WikimediaPageviews(fetch_json=_fetch)
    result = await source.get_pageviews("Tesla, Inc.", days=7)
    assert "Tesla%2C_Inc." in captured["url"]  # spaces → underscores, url-encoded
    assert result.article == "Tesla, Inc."
    assert result.total_views == 2500
    assert len(result.items) == 2
    assert result.items[0].views == 1000


async def test_pageviews_empty_notes():
    async def _fetch(url: str) -> dict:
        return {"items": []}

    result = await WikimediaPageviews(fetch_json=_fetch).get_pageviews("Nonexistent Article XYZ")
    assert result.items == []
    assert "exact Wikipedia article title" in result.note
