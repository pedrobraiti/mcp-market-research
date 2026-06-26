<p align="center">
  <strong>Scout</strong> — an MCP server that gathers and structures financial data for AI agents.
</p>

<p align="center">
  <em>Valet trades, Scout researches.</em> The <strong>senses</strong> layer of an agentic-trading
  stack — it gives an AI agent (like Claude Code) the data to research any US stock or ETF, in depth,
  from <strong>free</strong> sources. Pairs with
  <a href="https://github.com/pedrobraiti/mcp-ibkr-agent">mcp-ibkr-agent</a> (execution).
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT">
  <img src="https://img.shields.io/badge/tools-32-orange" alt="32 tools">
  <img src="https://img.shields.io/badge/status-live--validated-success" alt="Status: live-validated">
</p>

> **Not financial advice.** A research and data-gathering tool. It does **not** place orders and
> does **not** decide what to buy — that is the agent's and `mcp-ibkr-agent`'s job. Use at your own risk.

## What this is

**Scout** is an **MCP server** exposing **32 purpose-built tools** an AI agent calls to research a
company or market — quotes, fundamentals, technicals, options-implied volatility, SEC filings & XBRL
financials, macro, news, sentiment and attention — gathered from **free, keyless** data sources, in
parallel, returned as typed, structured data.

It is the **senses** layer of a three-part split:

- **Brain** — the agent (Claude Code), reasoning over the data and deciding *what/when* to invest.
- **Senses** — **Scout** (this repo): data & info gathering. **Stateless, data-only.**
- **Hands** — [`mcp-ibkr-agent`](https://github.com/pedrobraiti/mcp-ibkr-agent): execution on Interactive Brokers.

Scope: primarily **US equities & ETFs** (what the broker can trade). Every tool returns an
`{"ok": ..., "data": ...}` envelope and most accept an optional `as_of` (point-in-time) date.

> **Scout returns data, not reports.** It gives the agent the numbers and sources; the agent does the
> analysis and produces the output (e.g. a written report, a chart, a PDF). Ask your agent to
> *"research MU and write me a report/PDF"* and it will call Scout's tools, then compose the result itself.

## Quickstart

Scout is a **standard MCP server** — register it with any MCP-capable agent/client. The example
below uses Claude Code (the most common one); the steps are the same elsewhere, only the register
command differs.

```bash
# 1. Install
git clone https://github.com/pedrobraiti/mcp-market-research.git
cd mcp-market-research
python -m venv .venv
# Windows (PowerShell): & ".venv\Scripts\Activate.ps1"   (on a policy error: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)
# Linux/macOS:          source .venv/bin/activate
pip install -e .

# 2. (recommended) Configure — SEC EDGAR needs an identifiable User-Agent
cp .env.example .env      # then set SCOUT_SEC_USER_AGENT="Your Name your@email.com"

# 3. Register the MCP with Claude Code (use the venv's python — absolute path)
#   Windows:      claude mcp add scout -- "C:\path\to\mcp-market-research\.venv\Scripts\python.exe" -m scout.server.app
#   Linux/macOS:  claude mcp add scout -- /path/to/mcp-market-research/.venv/bin/python -m scout.server.app
```

The tools then appear to the agent (in Claude Code, a **new** session). Verify the data layer works
at any time, independent of any agent:

```bash
python -m scout.healthcheck AAPL   # live smoke test (fetches a real quote)
```

Then just ask the agent in natural language — e.g. *"Use the scout tools to do the most complete
analysis you can of a stock (say MU), then write it up as a PDF with charts."* The agent fans out
across the tools below, then composes the result itself.

**No API keys or logins required.** The only optional setting is `SCOUT_SEC_USER_AGENT` (SEC policy:
an identifiable User-Agent) — without it the SEC tools (`filings`, `sec_financials`, `filing_search`)
return a clear "please set it" message; everything else works keyless.

## Tools (32)

**Discovery — find names, not just look them up**
- `search_symbols(query, limit?)` — company name / partial ticker → symbols (the entry point).
- `market_movers(category?, limit?)` — market-wide top gainers / losers / most-active today.
- `sector_performance(period?, as_of?)` — total return of each US sector (SPDR ETFs) — rotation.
- `etf_holdings(symbol)` — an ETF's declared top holdings & sector weights (open a theme).
- `filing_search(query, forms?, limit?)` — full-text search across **all** SEC filings → companies by what they disclose (thesis → names).
- `news_search(query, limit?, days?)` — free-text news/event search across global media (**GDELT**).

**Company deep-dive**
- `company_dossier(symbol, depth?, as_of?)` — **flagship:** snapshot + fundamentals + dividends + technicals + earnings + analyst view + news, gathered **in parallel** (degrades gracefully).
- `company_snapshot(symbol, as_of?)` — price, day move, key multiples, sector/industry.
- `fundamentals(symbol, period?, as_of?)` — income/balance/cash-flow figures + derived margins.
- `quality_metrics(symbol, as_of?)` — ROE/ROA, margins, revenue & earnings growth and CAGR.
- `dividends(symbol, as_of?)` — payment history, trailing yield, growth streak, cut flag.
- `sec_financials(symbol, as_of?)` — **authoritative** annual financials from SEC XBRL (cross-check `fundamentals`).
- `filings(symbol, form_type?, limit?, as_of?)` — recent SEC EDGAR filings (10-K/10-Q/8-K …) with links.
- `earnings(symbol, as_of?)` — next earnings date + history (estimate / actual / surprise).
- `ownership(symbol)` — insider & institution %, top institutions, recent insider trades (13F/Form 4).

**Price & technicals**
- `price_history(symbol, period?, interval?, as_of?)` — OHLCV bars.
- `technicals(symbol, as_of?)` — SMA(50/200), EMA(20), RSI(14), MACD, ATR(14), 52-week range (raw numbers, no verdict).
- `relative_strength(symbols[], benchmark?, period?, as_of?)` — each name's return vs a benchmark.
- `options_volatility(symbol, expiry?)` — ATM implied vol + options-implied expected move.

**Sentiment & attention**
- `news(symbol, limit?)` — recent headlines (pairs with `extract`).
- `analyst_view(symbol)` — sell-side consensus & price targets (third-party opinion, as data).
- `retail_buzz(symbol?, limit?)` — Reddit (WSB/stocks) mention buzz (**ApeWisdom**) — retail attention.
- `wikipedia_attention(article, days?)` — daily Wikipedia pageviews — an attention proxy.

**Macro**
- `macro_context(as_of?)` — key US macro (**FRED**): Fed Funds, 10Y/2Y yields & spread, unemployment, CPI, VIX.
- `world_macro(country?, codes?)` — country-level macro (**World Bank**): GDP, inflation, unemployment…
- `treasury_data()` — official **US Treasury** figures: total public debt, average interest rates.

**Multi-symbol / portfolio (batch, stateless)**
- `compare(symbols[], as_of?)` — several names side by side (price, multiples, margins, sector).
- `correlation_matrix(symbols[], period?, as_of?)` — pairwise return correlation (real diversification).
- `classify(symbols[], as_of?)` — sector/industry/market-cap per symbol (to aggregate exposure).
- `news_digest(symbols[], limit_per_symbol?)` — headlines across a watchlist, newest first.
- `calendar(symbols[], as_of?)` — upcoming earnings & ex-dividend dates across symbols, sorted.

**Web**
- `extract(url)` — fetch a page → clean, token-efficient markdown (honestly reports paywalls/blocks).

## Architecture

Hexagonal (ports & adapters), mirroring `mcp-ibkr-agent`: the agent talks only to the MCP tools; each
data source is a swappable adapter behind a port, so a free source can be replaced or complemented
without touching the domain. Design principles (stateless, data-not-verdict, point-in-time) in
[DECISIONS.md](DECISIONS.md).

```
domain/      models + ports (the contracts)
adapters/    yfinance, SEC EDGAR, FRED, World Bank, US Treasury, GDELT, ApeWisdom, Wikimedia, web, stooq
research/    meta-tools that fan several ports out in parallel (dossier, compare, correlation, sectors…)
analytics.py source-agnostic indicator math (SMA/EMA/RSI/MACD/ATR, correlation)
server/      MCP server (FastMCP) + dependency composition
```

## Data sources (all free)

| Source | Provides | Key/login |
|---|---|---|
| **yfinance** | quotes, fundamentals, dividends, prices, options, news, analysts, ownership | none |
| **SEC EDGAR** | filings, XBRL financials, full-text search | User-Agent only |
| **FRED** | US macro (rates, CPI, unemployment, VIX) | none (keyless CSV) |
| **World Bank** | global country-level macro | none |
| **US Treasury** | public debt, average interest rates | none |
| **GDELT** | global news/event search | none |
| **ApeWisdom** | Reddit mention buzz | none |
| **Wikimedia** | Wikipedia pageviews (attention) | none |
| **stooq** | daily prices — transparent fallback for yfinance | none |

Paid free-tiers (Finnhub/FMP) are pluggable behind the same ports if ever wanted.

## Development

```bash
pip install -e ".[dev]"
pytest -q          # 96 offline tests
ruff check .       # lint
```

## License

MIT.
