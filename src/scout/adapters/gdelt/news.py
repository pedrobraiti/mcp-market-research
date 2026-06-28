"""GDELT DOC 2.0 implementation of ``NewsSearchSource`` — keyless, no API key.

GDELT indexes global news in near-real-time and exposes a keyless DOC API. Unlike the
symbol-based ``news`` tool (yfinance), this searches by FREE TEXT — a theme ("AI data center
power"), an event, or a company name — across worldwide media. Capture only: it returns
articles (title, source, date, link) for the agent to read via ``extract`` and judge.

The JSON fetch is injected for offline tests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from urllib.parse import quote

from ...domain.models import WebNewsItem, WebNewsSearch
from ..retry import SourceUnavailable, with_retry

_DOC_URL = (
    "https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode=artlist&format=json"
    "&maxrecords={limit}&timespan={days}d&sort=datedesc"
)


def _parse_seendate(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y%m%dT%H%M%SZ")
    except ValueError:
        return None


class GdeltNewsSearch:
    def __init__(
        self,
        fetch_json: Callable[[str], Awaitable[dict]] | None = None,
        timeout: float = 15.0,
        retry_attempts: int = 3,
        retry_base_delay: float = 0.5,
    ) -> None:
        self._timeout = timeout
        self._retry_attempts = retry_attempts
        self._retry_base_delay = retry_base_delay
        self._fetch_json = fetch_json or self._default_fetch_json

    async def _default_fetch_json(self, url: str) -> dict:
        import httpx

        headers = {"User-Agent": "scout-mcp/0.1 (research; +https://github.com/pedrobraiti)"}
        async with httpx.AsyncClient(timeout=self._timeout, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            if not response.text.strip():
                return {}
            return response.json()

    async def search_news(self, query: str, limit: int = 20, days: int = 7) -> WebNewsSearch:
        clean = query.strip()
        capped = max(1, min(limit, 75))
        days_window = max(1, min(days, 90))
        url = _DOC_URL.format(query=quote(clean), limit=capped, days=days_window)
        try:
            data = await with_retry(
                lambda: self._fetch_json(url),
                attempts=self._retry_attempts,
                base_delay=self._retry_base_delay,
            )
        except SourceUnavailable as exc:
            # A 429/timeout is "couldn't fetch", NOT "no news" — surface it so a downstream
            # gate retries/abstains instead of treating an empty list as a real absence.
            return WebNewsSearch(query=clean, items=[], source_status=exc.status)
        articles = (data or {}).get("articles") or []
        items: list[WebNewsItem] = []
        for article in articles[:capped]:
            if not isinstance(article, dict):
                continue
            items.append(
                WebNewsItem(
                    title=article.get("title"),
                    domain=article.get("domain"),
                    url=article.get("url"),
                    published=_parse_seendate(article.get("seendate")),
                    language=article.get("language"),
                    country=article.get("sourcecountry"),
                )
            )
        return WebNewsSearch(query=clean, items=items)
