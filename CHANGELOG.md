# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); the project predates semantic versioning, so
dates anchor the entries.

## [Unreleased]

### Added
- **Crypto spot senses (Tier 1) — 6 tools**, mirroring the equities side, all free & keyless:
  `crypto_quote`, `crypto_price_history`, `crypto_technicals` (CCXT public, ~100 exchanges),
  `crypto_asset_profile` (Coinpaprika: supply/market cap/rank/ATH), `crypto_fear_greed`
  (alternative.me Fear & Greed Index) and `crypto_buzz` (ApeWisdom `all-crypto` filter). Symbols use
  the CCXT `BASE/QUOTE` format (e.g. `BTC/USDT`) so a researched asset maps to a tradable pair;
  `crypto_technicals` reuses the existing `analytics.compute_technicals`. Read-only & external —
  Scout never reads an exchange account (that is the execution side's job). New config
  `SCOUT_CRYPTO_EXCHANGE` / `SCOUT_CRYPTO_QUOTE_CCY`; new dependency `ccxt`.
- **38 MCP tools** across 12 free, keyless data sources (yfinance, SEC EDGAR, FRED, World Bank,
  US Treasury, GDELT, ApeWisdom, Wikimedia, plus stooq as a price fallback; CCXT, Coinpaprika and
  alternative.me for crypto):
  - **Discovery:** `search_symbols`, `market_movers`, `sector_performance`, `etf_holdings`,
    `filing_search` (SEC full-text), `news_search` (GDELT).
  - **Company deep-dive:** `company_dossier`, `company_snapshot`, `fundamentals`, `quality_metrics`,
    `dividends`, `sec_financials` (XBRL), `filings`, `earnings`, `ownership`.
  - **Price & technicals:** `price_history`, `technicals`, `relative_strength`, `options_volatility`.
  - **Sentiment & attention:** `news`, `analyst_view`, `retail_buzz`, `wikipedia_attention`.
  - **Macro:** `macro_context` (FRED), `world_macro` (World Bank), `treasury_data` (US Treasury).
  - **Multi-symbol / portfolio:** `compare`, `correlation_matrix`, `classify`, `news_digest`, `calendar`.
  - **Web capture:** `extract` (URL → clean markdown).
- Stateless design with an optional point-in-time `as_of` on every research read.
- Hexagonal architecture (ports & adapters); each source is injectable for offline tests.
- `company_dossier` fans snapshot, fundamentals, dividends, technicals, earnings, analyst view
  and news out in parallel, degrading gracefully on partial failure.
- Indicator math (`analytics.py`): SMA/EMA/RSI/MACD/ATR, 52-week range, return correlation.
- Resilience: retry/backoff on yfinance, and a transparent **stooq fallback** for price history so
  a yfinance failure doesn't lose data.
- 114 offline tests; live-validated against every source.

### Fixed
- `dividends`: `had_cut` no longer flags a spurious cut from the **incomplete current calendar
  year** (a partial year has fewer ex-dates, so its lower calendar-year total is a timing
  artifact, not a real cut). Surfaced while validating a real MU equity-research report.

### Changed
- `quality_metrics`: docstring now states ROE/ROA/margins are the provider's **trailing-twelve-month**
  figures and will not reconcile with a single fiscal-year statement (only CAGR is statement-derived).

### Notes
- **Keyless by default.** No source requires a login or API key; SEC EDGAR only needs an
  identifiable `SCOUT_SEC_USER_AGENT` (its policy), not an account.
- Alpha Vantage (25 req/day) and Finnhub (free but needs an API key) were evaluated and **deferred**
  to keep the keyless, login-free experience. They remain pluggable behind the existing ports.
