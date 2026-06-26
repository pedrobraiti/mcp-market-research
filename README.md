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

🚧 **Early.** Architecture is locked (data MCP + strategy skill, Claude Code as the brain) and the first tools are working: yfinance + SEC EDGAR adapters behind ports, exposed as MCP tools, with offline tests and live-validated. More tools are next — see [DECISIONS.md](DECISIONS.md) for the design principles.

## Tools (today)

- `company_dossier(symbol, depth?, as_of?)` — flagship: snapshot + fundamentals + dividends + technicals + earnings + analyst view + news gathered **in parallel**, degrades gracefully if one source is down.
- `search_symbols(query, limit?)` — resolve a company name / partial ticker to symbols (the entry point).
- `market_movers(category?, limit?)` — market-wide top gainers / losers / most-active (discovery without a symbol).
- `compare(symbols[], as_of?)` — several names side by side (price, multiples, margins, sector).
- `correlation_matrix(symbols[], period?, as_of?)` — pairwise return correlation (real diversification).
- `classify(symbols[], as_of?)` — sector/industry/market-cap per symbol (to aggregate exposure).
- `news_digest(symbols[], limit_per_symbol?)` — headlines across a watchlist, newest first.
- `calendar(symbols[], as_of?)` — upcoming earnings & ex-dividend dates across symbols, sorted.
- `company_snapshot(symbol, as_of?)` — price, day move, key multiples, sector/industry.
- `fundamentals(symbol, period?, as_of?)` — income/balance/cash-flow figures + derived margins.
- `quality_metrics(symbol, as_of?)` — ROE/ROA, margins, revenue & earnings growth and CAGR.
- `relative_strength(symbols[], benchmark?, period?, as_of?)` — each name's return vs a benchmark.
- `dividends(symbol, as_of?)` — payment history, trailing yield, growth streak, cut flag.
- `news(symbol, limit?)` — recent headlines (title, publisher, date, link) — pairs with `extract`.
- `news_search(query, limit?, days?)` — free-text news/event search across global media (**GDELT**, keyless) — by theme or company name.
- `earnings(symbol, as_of?)` — next earnings date + history (estimate / actual / surprise).
- `options_volatility(symbol, expiry?)` — ATM implied vol + options-implied expected move to expiry.
- `analyst_view(symbol)` — sell-side consensus & price targets (third-party opinion, as data).
- `ownership(symbol)` — insider & institution %, top institutions, recent insider trades (13F/Form 4).
- `retail_buzz(symbol?, limit?)` — Reddit (WSB/stocks) mention buzz (**ApeWisdom**, keyless) — retail attention.
- `price_history(symbol, period?, interval?, as_of?)` — OHLCV bars.
- `technicals(symbol, as_of?)` — SMA(50/200), EMA(20), RSI(14), MACD, ATR(14), 52-week high/low (raw numbers, no trend verdict).
- `sector_performance(period?, as_of?)` — total return of each US sector (via SPDR ETFs) — rotation.
- `etf_holdings(symbol)` — an ETF's declared top holdings & sector weights (open a theme).
- `macro_context(as_of?)` — key US macro from **FRED** (Fed Funds, 10Y/2Y yields, 10Y-2Y spread, unemployment, CPI, VIX); no API key needed.
- `world_macro(country?, codes?)` — country-level macro from the **World Bank** (GDP, inflation, unemployment…), keyless.
- `treasury_data()` — official US **Treasury** figures (total public debt, average interest rates), keyless.
- `filings(symbol, form_type?, limit?, as_of?)` — recent **SEC EDGAR** filings (10-K/10-Q/8-K …) with links to the primary document (authoritative source; needs `SCOUT_SEC_USER_AGENT`).
- `sec_financials(symbol, as_of?)` — authoritative annual financials from **SEC EDGAR XBRL** (revenue, income, assets, equity) with per-line provenance — to **cross-check** `fundamentals` against the primary source.
- `extract(url)` — fetch a web page and return its **main content as clean markdown** (a research aid; honestly reports paywalls/blocks instead of faking).

Every tool returns an `{"ok": ..., "data": ...}` envelope and accepts an optional `as_of`
(point-in-time) so the agent can compose two stateless reads into a "what changed since" diff.

## Architecture

Hexagonal (ports & adapters), mirroring `mcp-ibkr-agent`: the agent talks only to the MCP tools; each data source is a swappable adapter behind a port, so a free source can be replaced or complemented by another without touching the domain.

```
domain/      models (CompanySnapshot, Fundamentals, DividendHistory, FilingsList, ...) and ports
adapters/    yfinance + SEC EDGAR (today); FRED, stooq, ... next — one adapter per source
research/    meta-tools that fan several ports out in parallel (company_dossier)
server/      MCP server (FastMCP) + dependency composition
```

## Stack

- **Python 3.12+**
- **MCP server** (FastMCP)
- Free, keyless data sources: **yfinance** (market/fundamentals/dividends/prices/options), **SEC EDGAR** (filings + XBRL), **FRED** (US macro), **World Bank** (global macro), **US Treasury** (fiscal), **GDELT** (global news), **ApeWisdom** (Reddit buzz). **stooq** is a transparent price-history fallback when yfinance fails. Paid free-tiers (Finnhub/FMP) are pluggable behind the same ports.

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
