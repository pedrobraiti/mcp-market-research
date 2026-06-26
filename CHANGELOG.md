# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); the project predates semantic versioning, so
dates anchor the entries.

## [Unreleased]

### Added
- **16 MCP tools** across four free data sources:
  - Discovery: `search_symbols`, `compare`, `correlation_matrix`.
  - Company (yfinance): `company_dossier`, `company_snapshot`, `fundamentals`, `dividends`,
    `price_history`, `technicals`, `news`, `earnings`, `analyst_view`.
  - Macro (FRED, keyless): `macro_context`.
  - Filings & financials (SEC EDGAR + XBRL): `filings`, `sec_financials`.
  - Web capture: `extract` (URL → clean markdown).
- Stateless design with an optional point-in-time `as_of` on every research read.
- Hexagonal architecture (ports & adapters); each source is injectable for offline tests.
- `company_dossier` fans snapshot, fundamentals, dividends, technicals, earnings, analyst view
  and news out in parallel, degrading gracefully on partial failure.
- Indicator math (`analytics.py`): SMA/EMA/RSI/MACD/ATR, 52-week range, return correlation.
- Retry/backoff on the yfinance adapter so a transient block isn't mistaken for a missing symbol.
