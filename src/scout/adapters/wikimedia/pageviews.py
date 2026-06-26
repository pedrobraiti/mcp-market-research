"""Wikimedia Pageviews implementation — keyless attention proxy.

Daily Wikipedia pageviews for a company's article are an official, stable proxy for public
attention (like Google Trends, but reliable and keyless). Rising views = a name is in the public
eye. Capture only — raw counts the agent interprets. Wikimedia requires a descriptive User-Agent.

The JSON fetch is injected for offline tests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import date, datetime, timedelta
from urllib.parse import quote

from ...domain.models import PageviewDay, WikipediaAttention

_URL = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/"
    "all-access/all-agents/{article}/daily/{start}/{end}"
)


def _parse_timestamp(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:8], "%Y%m%d").date()
    except ValueError:
        return None


class WikimediaPageviews:
    def __init__(
        self,
        fetch_json: Callable[[str], Awaitable[dict]] | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._timeout = timeout
        self._fetch_json = fetch_json or self._default_fetch_json

    async def _default_fetch_json(self, url: str) -> dict:
        import httpx

        headers = {"User-Agent": "scout-mcp/0.1 (research; +https://github.com/pedrobraiti)"}
        async with httpx.AsyncClient(timeout=self._timeout, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_pageviews(self, article: str, days: int = 30) -> WikipediaAttention:
        window = max(1, min(days, 365))
        title = quote(article.strip().replace(" ", "_"), safe="")
        end = date.today()
        start = end - timedelta(days=window)
        url = _URL.format(article=title, start=start.strftime("%Y%m%d"), end=end.strftime("%Y%m%d"))
        data = await self._fetch_json(url)
        rows = (data or {}).get("items") or []
        items: list[PageviewDay] = []
        total = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            day = _parse_timestamp(row.get("timestamp"))
            views = row.get("views")
            if day is None:
                continue
            view_count = int(views) if isinstance(views, int | float) else None
            if view_count is not None:
                total += view_count
            items.append(PageviewDay(day=day, views=view_count))
        note = None if items else "No pageviews — check the exact Wikipedia article title."
        return WikipediaAttention(
            article=article.strip(),
            days=window,
            total_views=total if items else None,
            items=items,
            note=note,
        )
