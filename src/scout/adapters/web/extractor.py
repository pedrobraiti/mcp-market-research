"""Web content extractor — URL → clean, token-efficient markdown.

A capture *sense* for the agent's own research (see DECISIONS ADR-005): the agent decides which
URLs matter; this fetches them and returns just the main content, dropping nav/boilerplate so the
agent reads more signal per token. It never summarizes or judges — that is the brain's job.

The fetch (httpx) is injected so the unit tests run fully offline; the markdown conversion uses
trafilatura, imported lazily so a test that injects HTML needs neither the network nor the lib.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable

from ...domain.models import ExtractedPage

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


class WebExtractor:
    def __init__(
        self,
        user_agent: str,
        fetch: Callable[[str], Awaitable[tuple[int, str]]] | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._user_agent = user_agent
        self._timeout = timeout
        self._fetch = fetch or self._default_fetch

    async def _default_fetch(self, url: str) -> tuple[int, str]:
        import httpx

        headers = {"User-Agent": self._user_agent, "Accept-Language": "en-US,en;q=0.9"}
        async with httpx.AsyncClient(
            timeout=self._timeout, headers=headers, follow_redirects=True
        ) as client:
            response = await client.get(url)
            return response.status_code, response.text

    async def extract(self, url: str) -> ExtractedPage:
        try:
            status, html = await self._fetch(url)
        except Exception as exc:  # noqa: BLE001
            return ExtractedPage(
                url=url, fetched_ok=False, note=f"fetch failed ({type(exc).__name__}): {exc}"
            )

        if status != 200 or not html:
            return ExtractedPage(
                url=url,
                fetched_ok=False,
                status_code=status,
                note=f"HTTP {status} — the page may be paywalled or blocking automated access.",
            )

        title = _extract_title(html)
        markdown = await asyncio.to_thread(_to_markdown, html, url)
        if not markdown:
            return ExtractedPage(
                url=url,
                fetched_ok=True,
                status_code=status,
                title=title,
                note="Fetched, but no main content could be extracted (e.g. a JS-rendered page).",
            )
        return ExtractedPage(
            url=url,
            fetched_ok=True,
            status_code=status,
            title=title,
            markdown=markdown,
            char_count=len(markdown),
        )


def _extract_title(html: str) -> str | None:
    match = _TITLE_RE.search(html)
    if not match:
        return None
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title or None


def _to_markdown(html: str, url: str) -> str | None:
    import trafilatura

    return trafilatura.extract(
        html,
        output_format="markdown",
        include_links=True,
        include_tables=True,
        favor_recall=True,
        url=url,
    )
