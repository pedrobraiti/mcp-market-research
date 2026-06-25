<p align="center">
  <strong>Scout</strong> — an MCP server that gathers and structures financial data for AI trading agents.
</p>

<p align="center">
  <em>Valet trades, Scout researches.</em> Pairs with
  <a href="https://github.com/pedrobraiti/mcp-ibkr-agent">mcp-ibkr-agent</a> (execution) to give an
  AI agent both senses and hands — while the investment <strong>decision</strong> stays with the agent and your strategy skill.
</p>

> ⚠️ **Not financial advice.** A research and data-gathering tool. It does not place orders — that is `mcp-ibkr-agent`'s job. Use at your own risk.

## What this is

**Scout** is an **MCP server** that exposes purpose-built, consolidated tools an AI agent (like Claude Code) calls to research a company or market: quotes, fundamentals, technicals, SEC filings, macro context and news — gathered from **free data sources**, in parallel, returned as structured dossiers.

It is the **senses** layer of a larger agentic-trading ecosystem:

- **Brain** — Claude Code, reasoning over the data and deciding *what/when* to invest (via a strategy skill).
- **Senses** — **Scout** (this repo): data & info gathering.
- **Hands** — [`mcp-ibkr-agent`](https://github.com/pedrobraiti/mcp-ibkr-agent): reliable execution on Interactive Brokers.

The scope (for now) is the universe Interactive Brokers can trade — primarily **US equities and ETFs**.

## Status

🚧 **Early.** Architecture is locked (data MCP + strategy skill, Claude Code as the brain) and the first vertical slice is working: a yfinance adapter behind a port, exposed as three MCP tools, with offline tests and live-validated. More tools are next — see `docs/tool-brainstorm.md` for the planned surface and design principles.

## Tools (today)

- `company_snapshot(symbol, as_of?)` — price, day move, key multiples, sector/industry.
- `fundamentals(symbol, period?, as_of?)` — income/balance/cash-flow figures + derived margins.
- `dividends(symbol, as_of?)` — payment history, trailing yield, growth streak, cut flag.

Every tool returns an `{"ok": ..., "data": ...}` envelope and accepts an optional `as_of`
(point-in-time) so the agent can compose two stateless reads into a "what changed since" diff.

## Architecture

Hexagonal (ports & adapters), mirroring `mcp-ibkr-agent`: the agent talks only to the MCP tools; each data source is a swappable adapter behind a port, so a free source can be replaced or complemented by another without touching the domain.

```
domain/      models (CompanySnapshot, Fundamentals, DividendHistory, ...) and ports (data sources)
adapters/    yfinance (today); SEC EDGAR, FRED, ... next — one adapter per source
server/      MCP server (FastMCP) + dependency composition
```

## Stack

- **Python 3.12+**
- **MCP server** (FastMCP)
- Free data sources first: **yfinance** (live), then **SEC EDGAR**, **FRED**, **stooq** (paid free-tiers like Finnhub/FMP/Alpha Vantage are pluggable later)

## Develop

```bash
python -m venv .venv
# Windows (PowerShell): & ".venv\Scripts\Activate.ps1"
pip install -e ".[dev]"
pytest -q                 # offline tests
ruff check .              # lint
python -m scout.healthcheck AAPL   # live smoke test (hits yfinance)
```

Register with Claude Code: `claude mcp add scout -- /path/to/.venv/Scripts/python.exe -m scout.server.app`

## License

MIT.
