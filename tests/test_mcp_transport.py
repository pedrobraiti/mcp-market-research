"""Smoke tests over the REAL MCP stdio transport — the regression net for the v0.5.3 bug class.

The first-call hang (Session 8: yfinance's curl_cffi/crumb setup and ccxt's first
``load_markets`` deadlock when they first run under FastMCP's async server) ONLY reproduces
over the real transport — spawning ``python -m scout.server.app`` and speaking MCP over stdio.
It never showed through the service layer or plain-asyncio unit tests, which is why no test
caught it. These tests keep that lesson encoded:

* the server must start, complete the MCP handshake and list its tools within a bounded time;
* the FIRST yfinance-path call and the FIRST ccxt-path call must RESPOND (any envelope,
  including an honest error) instead of hanging.

Network honesty: the data calls assert "responds in bounded time", NOT "returns data" — a 429
or an offline DNS failure comes back quickly as an error envelope and still PASSES. Only a
hang or a dead server fails. So the tests are CI-safe and pass offline too.
"""

from __future__ import annotations

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Startup includes the best-effort warm-up (bounded ~10s/request; typically ~5s with network,
# fast-fail without). The hang this guards against was >40s per call and unbounded in practice,
# so a generous ceiling still separates "working" from "hung" unambiguously.
_TRANSPORT_TIMEOUT_S = 120

_EXPECTED_TOOL_COUNT = 62  # bump when adding tools — this is the drift tripwire


async def _exercise_transport() -> tuple[list[str], object, object]:
    params = StdioServerParameters(command=sys.executable, args=["-m", "scout.server.app"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = [tool.name for tool in listed.tools]
            # First call down each lazy-setup path (the exact v0.5.3 hang classes):
            # yfinance (worker-thread blocking call) and ccxt (loop-bound aiohttp client).
            yf_result = await session.call_tool(
                "price_history", {"symbol": "SPY", "period": "5d"}
            )
            ccxt_result = await session.call_tool("crypto_quote", {"symbol": "BTC/USDT"})
            return names, yf_result, ccxt_result


def test_mcp_stdio_handshake_tools_and_first_calls() -> None:
    names, yf_result, ccxt_result = asyncio.run(
        asyncio.wait_for(_exercise_transport(), timeout=_TRANSPORT_TIMEOUT_S)
    )
    assert len(names) == _EXPECTED_TOOL_COUNT
    assert "price_history" in names
    assert "crypto_quote" in names
    # Responding at all is the assertion — content may be data or an honest error envelope.
    assert yf_result.content
    assert ccxt_result.content
