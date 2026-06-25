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

🚧 **Early setup.** Architecture is locked (data MCP + strategy skill, Claude Code as the brain); the tool surface and the first data adapter are next. See the design notes in the project memory.

## Planned architecture

Hexagonal (ports & adapters), mirroring `mcp-ibkr-agent`: the agent talks only to the MCP tools; each data source is a swappable adapter behind a port, so a free source can be replaced by a paid one later without touching the domain.

```
domain/      models (Dossier, Fundamentals, Technicals, Filing, MacroSnapshot) and ports (data sources)
adapters/    yfinance, SEC EDGAR, FRED, ... — one adapter per source
server/      MCP server (FastMCP) + dependency composition
```

## Stack

- **Python 3.12+**
- **MCP server** (FastMCP)
- Free data sources first: **yfinance**, **SEC EDGAR**, **FRED**, **stooq** (paid free-tiers like Finnhub/FMP/Alpha Vantage are pluggable later)

## License

MIT.
