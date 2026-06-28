# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); the project predates semantic versioning, so
dates anchor the entries.

## [Unreleased]

### Added
- **Full crypto spot layer — 21 tools**, mirroring the equities side, all free & keyless. Symbols
  use the CCXT `BASE/QUOTE` format (e.g. `BTC/USDT`) so a researched asset maps to a tradable pair.
  Read-only & external — Scout never reads an exchange account (that is the execution side's job).
  New config `SCOUT_CRYPTO_EXCHANGE` / `SCOUT_CRYPTO_QUOTE_CCY`; new dependency `ccxt`.
  - **Price/technicals/discovery:** `crypto_quote`, `crypto_price_history`, `crypto_technicals`
    (reuses `analytics.compute_technicals`), `crypto_search`, `crypto_movers`, `crypto_order_book`,
    `crypto_compare`, `crypto_correlation_matrix`, `crypto_relative_strength` (CCXT, Coinpaprika).
  - **Fundamentals/derivatives/sentiment:** `crypto_dossier` (flagship parallel fan-out),
    `crypto_asset_profile` (Coinpaprika), `crypto_onchain` (mempool.space BTC / Blockscout ETH),
    `crypto_derivatives` (Binance/Bybit/OKX funding & OI — context only), `crypto_implied_vol`
    (Deribit DVOL), `crypto_fear_greed` (alternative.me), `crypto_buzz` (ApeWisdom `all-crypto`).
  - **DeFi/macro:** `crypto_macro` & `crypto_sectors` (CoinGecko), `defi_overview`,
    `stablecoin_supply`, `defi_yields` (DefiLlama).
- **53 MCP tools** across 17 free, keyless data sources (yfinance, SEC EDGAR, FRED, World Bank,
  US Treasury, GDELT, ApeWisdom, Wikimedia, plus stooq as a price fallback; and for crypto: CCXT,
  Coinpaprika, alternative.me, mempool.space, Blockscout, Binance/Bybit/OKX, Deribit, DefiLlama,
  CoinGecko):
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
- **Derived risk/volatility/momentum layer** on `technicals` & `crypto_technicals` (same pure
  `analytics.py`, no new deps, no new tools — additive fields, each null until its own minimum
  sample is met): annualized realized volatility (close-to-close) and an OHLC estimator
  (**Yang-Zhang** for equities, **Rogers-Satchell** for gapless 24/7 crypto), `atr_pct`,
  52-week range position, **Sharpe / Sortino / Calmar**, max drawdown (+ underwater bars),
  return skew & excess kurtosis, and momentum (3m/6m/12m and the 12-1 factor). Asset-class
  aware: ratios annualize at 252 (equities) / 365 (crypto), surfaced via `annualization_factor`.
  Turns OHLCV the Scout already fetched — but previously reduced to the close — into decision-grade
  risk numbers. See ADR-006.
- **Derived macro regime layer** on `macro_context`: the FRED adapter already downloaded each full
  series and then kept only the last point — it now also returns a `derived` block computed from
  those same series (no new sources beyond adding `DGS3MO`): **CPI inflation YoY** and 3-month
  annualized (a raw CPI index level is meaningless alone), **real Fed-funds & real 10y** (ex-post),
  the **Sahm recession gap** (+ signal), **VIX z-score & percentile** vs its ~1y window, **yield-curve
  inversion** (+ consecutive observations inverted), and a **12-month recession probability** (NY-Fed
  Estrella-Mishkin term-spread probit, via stdlib `math.erf`). Stays measures-not-verdicts. See ADR-007.
- **Macro layer extended** with three more FRED series and their reads: 10y **breakeven inflation**
  (`T10YIE` → market-expected CPI), the 10y **TIPS real yield** (`DFII10` → ex-ante real rate), and
  the US **high-yield credit spread** (`BAMLH0A0HYM2`) with a **z-score** vs its ~1y window — a
  financial-stress gauge that often widens before equities fall. See ADR-007.
- **Derived fundamentals layer** on `fundamentals`, `analyst_view` and `earnings`, from figures
  already fetched (the balance sheet was loaded but total assets / equity went unread; the option
  chain analogue here is the raw statement). `fundamentals` now also surfaces total assets,
  stockholders' equity and (on a live read) market cap, plus: **net_debt**, **net_debt_to_fcf**,
  **fcf_margin**, **gross_profitability** (Novy-Marx) and **pretax ROIC** (statement-only), and —
  paired with current market cap on a live read — **FCF & earnings yield**, **enterprise value**
  and **EV/EBIT, EV/Sales, EBIT/EV** (Greenblatt). `analyst_view` adds **upside_pct** and
  **target_dispersion** (consensus tightness). `earnings` adds **beat_rate**, **surprise_streak**,
  **avg_surprise** and **surprise_consistency**. Cap-based ratios are null on a point-in-time
  (`as_of`) read — the source has no historical market cap to pair with a past statement — and any
  ratio is null when its denominator isn't positive. See ADR-008.
- **Fundamentals extended** with liquidity/leverage/coverage from more of the same statements:
  current assets/liabilities, retained earnings, D&A and interest expense are now read, giving
  **current_ratio**, **working_capital**, **debt_to_equity**, **EBITDA** (EBIT + D&A) → **EV/EBITDA**
  and **net_debt_to_ebitda**, **interest_coverage**, and the **Altman Z″** distress score (book-equity
  variant — no market cap needed, so it works on a point-in-time read). Null where a line is missing
  or a divisor isn't positive. See ADR-008.
- **Derived crypto microstructure/derivatives layer** on `crypto_derivatives` and
  `crypto_order_book`, from data already fetched and discarded. `crypto_derivatives` now adds a
  per-venue **annualized funding rate** and cross-venue aggregates: **OI-weighted funding
  consensus** (and annualized), **funding dispersion** across venues (a stress/arbitrage signal)
  and **total open interest in USD** (using the per-venue USD OI the adapter already computes, so
  no unit-mismatch). `crypto_order_book` adds **imbalance** ((bid−ask depth)/(bid+ask)) and
  **microprice** (size-weighted fair price). Annualized funding assumes the venues' 8h interval
  (a single next-funding snapshot can't reveal the true interval) and flags it in `note`. See
  ADR-009.
- **DVOL regime read** on `crypto_implied_vol`: the current DVOL's **z-score and percentile** vs a
  trailing ~6-month window (extended from ~1 month for a meaningful regime) — the crypto analogue of
  the VIX z-score, self-contained from DVOL's own history. See ADR-009.
- **Crypto cycle/tokenomics measures:** the **Mayer Multiple** (price / SMA-200) on `technicals`
  and `crypto_technicals` — both inputs were already computed — and tokenomics ratios on
  `crypto_asset_profile`: **float_ratio** (circulating/total), **issuance_progress**
  (circulating/max) and **future_dilution** ((max−circulating)/circulating). Max-based ratios are
  null for uncapped assets (no max supply). The circulating-based ratios populate only when the
  source reports circulating supply (the free Coinpaprika tier currently returns it null for some
  assets — they degrade to null rather than erroring). See ADR-010.
- **Stablecoin Supply Ratio & dominance** on `crypto_macro`: joined with the DefiLlama stablecoin
  total — SSR (total mcap / Σ stablecoins; low = lots of sidelined "dry powder") and stablecoin
  dominance (cash share of the market). The join is supplementary: a stablecoin-source failure leaves
  the ratios null and never sinks the macro read. See ADR-010.
- **Derived options layer** on `options_volatility`, from the chain already fetched (only ATM IV
  was used before): **iv_skew** (OTM put vs call IV over ATM — >0 = puts richer/fear), **put/call
  ratios** (volume & open interest), and the **volatility risk premium** — ATM IV minus trailing
  realized vol — with **iv_rv_ratio** (>1 = options look rich). The VRP is the stateless stand-in
  for IV rank; true IV-rank/percentile need stored IV history a stateless server can't keep, so
  they're omitted. Illiquid wings (IV ≤ 0) are skipped so skew isn't built on garbage. See ADR-011.
- Resilience: retry/backoff on yfinance, and a transparent **stooq fallback** for price history so
  a yfinance failure doesn't lose data.
- 145 offline tests; live-validated against every source.

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
