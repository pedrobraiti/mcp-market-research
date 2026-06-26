from scout.adapters.web import WebExtractor

_ARTICLE_HTML = """
<html>
<head><title>  Acme Corp Reports Record Q2 Revenue  </title></head>
<body>
<nav>Home | About | Contact | Subscribe</nav>
<article>
<h1>Acme Corp Reports Record Q2 Revenue</h1>
<p>Acme Corporation announced today that quarterly revenue rose to 4.2 billion dollars,
an increase of 28 percent compared with the same period a year earlier, driven by strong
demand for its industrial automation products across North America and Europe.</p>
<p>Operating margin expanded to 19 percent from 16 percent, and the company raised its
full-year guidance, citing a record order backlog and easing supply-chain constraints that
had previously weighed on shipments of its flagship controllers.</p>
<p>Management said free cash flow reached 900 million dollars for the quarter and that the
board approved a new share repurchase authorization of up to two billion dollars over the
next two years, reflecting confidence in the durability of the demand environment.</p>
</article>
<footer>Copyright 2026 Acme Corp. All rights reserved.</footer>
</body>
</html>
"""


def _make(fetch):
    return WebExtractor("test-agent", fetch=fetch)


async def test_extracts_main_content_as_markdown():
    async def fetch_ok(url):
        return 200, _ARTICLE_HTML

    page = await _make(fetch_ok).extract("https://example.com/acme")
    assert page.fetched_ok is True
    assert page.status_code == 200
    assert page.title == "Acme Corp Reports Record Q2 Revenue"
    assert page.markdown is not None
    assert "4.2 billion dollars" in page.markdown
    # Boilerplate (nav/footer) should be dropped from the main content.
    assert "Subscribe" not in page.markdown
    assert page.char_count == len(page.markdown)


async def test_blocked_page_reports_honestly():
    async def fetch_403(url):
        return 403, ""

    page = await _make(fetch_403).extract("https://paywalled.example.com/x")
    assert page.fetched_ok is False
    assert page.status_code == 403
    assert page.markdown is None
    assert "403" in page.note


async def test_fetch_exception_is_caught():
    async def fetch_boom(url):
        raise RuntimeError("connection reset")

    page = await _make(fetch_boom).extract("https://example.com/x")
    assert page.fetched_ok is False
    assert "connection reset" in page.note
