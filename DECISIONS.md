# Architecture Decision Records

The key technical decisions behind Scout and the *why*. Append-only: older entries are not
edited, so the reasoning trail stays honest. (Internal, more granular notes are kept out of
this public log.)

---

## ADR-001 — Scope: a stateless data/research MCP (the "senses")

**Decision.** Scout is an MCP server that **gathers and structures financial data** for an AI
agent. It does not place orders and does not decide what to buy or sell.

**Why.** It is one piece of a three-part split: **execution** lives in a separate broker MCP
([agentic-trading-mcp](https://github.com/pedrobraiti/agentic-trading-mcp), the "hands"), **decisions**
live in the calling agent / strategy skill (the "brain"), and Scout is the **senses**. Keeping
data capture independent of both keeps each piece simple, testable and swappable.

---

## ADR-002 — Hexagonal architecture, free data sources first

**Decision.** Define ports (`MarketDataSource`, `FilingsSource`, …) and implement them with
**free** sources — yfinance (market/fundamentals/dividends) and SEC EDGAR (filings) today;
FRED, stooq and others next. Paid providers are pluggable later behind the same ports.

**Why.** Robustness comes from the design, not from one vendor. Each source is an adapter, so
a flaky or limited source can be complemented or replaced without touching the domain. yfinance
is a great breadth-first default but is an unofficial scraper with rate limits and gaps — so the
architecture is built to **cross-check** it (e.g. SEC EDGAR as the authoritative primary source).

---

## ADR-003 — Stateless, with point-in-time (`as_of`) reads

**Decision.** Scout persists no user state. Every research tool accepts an optional `as_of`
date and otherwise returns the latest read.

**Why.** A data MCP being stateless is a feature: the same call returns the same world, with no
second source of truth to sync. `as_of` lets the agent compose two stateless reads into a "what
changed since" diff without Scout ever storing the date — memory (theses, watchlists) belongs to
the agent/skill, not to the senses.

---

## ADR-004 — Tools calculate, they don't conclude

**Decision.** Tools return data and explicit measures, never a verdict. There is no
"is this a buy?", no embedded "fair price", no "who benefits". Fat, purposeful tools
(`company_dossier`) are allowed — they aggregate several reads in parallel — but they only
consolidate data, never judge.

**Why.** Judgment is the agent's job. Pushing it into a tool would make the data layer opaque
and untrustworthy. Data + an explicit ruler keeps every output auditable; the conclusion stays
with the brain.

---

## ADR-005 — Research is the agent's job; Scout offers capture senses

**Decision.** Scout does not expose a "deep research" tool that returns a synthesized report.
Deep research (deciding what to investigate, reading, cross-checking, concluding) is the agent's
work. Scout's role is to provide the **capture senses** that make that research cheaper and more
complete — e.g. fetching and cleanly extracting page content.

**Why.** Validated by a blind benchmark: an agent's own multi-source research came out
essentially on par with a dedicated web-research product, converging on the same primary facts.
The remaining gap was mostly **fetching primary sources** — a capture problem a clean extraction
tool addresses — not a synthesis problem. So research stays in the brain; Scout sharpens its eyes.

---

## ADR-006 — Derive risk numbers from OHLCV the agent already pays for

**Decision.** `technicals`/`crypto_technicals` now also return a derived risk/volatility/momentum
layer (realized & OHLC volatility, Sharpe/Sortino/Calmar, max drawdown, skew/kurtosis, momentum)
computed in `analytics.py`. This stays within ADR-004: they are explicit measures, not verdicts —
Scout reports a Sharpe of 0.66 and a −33% drawdown, it never says "good risk" or "buy".

**Why.** Scout already fetched full OHLCV and then collapsed it to the close for SMA/RSI/etc.,
leaving the open/high/low and the whole return distribution on the floor. Recomputing this layer
in the agent or the skill would mean every consumer re-deriving the same math from raw bars (and
getting the annualization wrong). Putting it in the deterministic data layer makes it correct once,
auditable, and free to whoever calls the tool.

**Choices that matter.**
- **Asset-class aware annualization.** Ratios annualize at 252 (equities trading days) vs 365
  (crypto 24/7); the chosen factor is surfaced as `annualization_factor` so the number is never
  ambiguous. Getting this wrong inflates crypto vol by ~20%.
- **Estimator by market structure.** OHLC volatility uses **Yang-Zhang** for equities (it models
  the overnight gap, the most efficient estimator when gaps exist) and **Rogers-Satchell** for
  crypto (no overnight gap in a 24/7 market, so the gap term degenerates). The estimator used is
  reported in `volatility_estimator`.
- **Pure-Python, no new deps.** All of it is stdlib arithmetic (no numpy/pandas/scipy), keeping
  `analytics.py` offline-unit-testable and the install light. Each field returns `null` below its
  own minimum sample rather than emitting a noisy, meaningless number.
- **Stateless-respecting.** Only metrics computable from a single on-demand price-history read are
  included. Metrics that need stored history (e.g. IV-rank from an implied-vol time series) were
  deliberately left out — they would break ADR-003.

---

## ADR-007 — Transform the FRED series instead of shipping raw index levels

**Decision.** `macro_context` now returns a `derived` block alongside the raw indicators: CPI YoY
& 3-month annualized, ex-post real Fed-funds & real 10y, the Sahm recession gap (+ signal), VIX
z-score & percentile, yield-curve inversion (+ duration) and a 12-month recession probability
(Estrella-Mishkin probit). One new series (`DGS3MO`) was added to feed the probit.

**Why.** The FRED adapter was already downloading each series' *entire* CSV history and then
throwing all but the last point away. A raw level is often useless on its own — a CPI index of
`333.979` tells the agent nothing; `CPI YoY = 4.2%, 3m annualized 9.4% (reaccelerating)` is a
decision. The history needed to compute it was already in hand and free; collapsing it to the
latest point was the waste. Doing the transform here (not in the skill) means it is correct once
and auditable, and the agent never has to re-derive YoY/real-rate/Sahm math from a level.

**Choices that matter.**
- **Same ADR-004 line.** It reports a recession probability and a Sahm gap; it never says "go to
  cash". Measures, not a regime verdict.
- **Honest about the proxy.** The NY-Fed probit is calibrated on the 10y-3m spread using
  *monthly averages*; Scout feeds it the latest daily spread and says so in `notes`. Better an
  explicit, slightly-approximate number with its caveat than silence.
- **Guarded, never fabricated.** Each block needs its minimum history (e.g. ≥13 monthly CPI points
  for YoY) or its field stays `null` — a short series yields nothing rather than a misleading number.
- **Pure-Python, stdlib only.** The probit's normal CDF uses `math.erf`; no scipy. Generic stats
  (z-score, percentile, Sahm, probit) live in `analytics.py`; only the date alignment lives in the
  adapter. Stateless is preserved — everything is computed from a single on-demand read.
- **Followed up (was M2b).** Breakeven inflation (`T10YIE`), ex-ante real yield (`DFII10`) and the
  high-yield credit spread (`BAMLH0A0HYM2`) were later added: they surface as raw indicators and as
  derived fields (`inflation_expectations_10y`, `real_10y_exante`, `credit_spread_hy` + its z-score
  for the stress regime). The credit-spread z-score is the derived-math win — HY OAS widens before
  equities fall, so its regime read is high-value.

---

## ADR-008 — Derive valuation/solvency/quality from statements already fetched

**Decision.** `fundamentals` returns a derived block (net debt & net-debt/FCF, FCF margin,
gross profitability, pretax ROIC, and — on a live read — FCF & earnings yield, enterprise value,
EV/EBIT, EV/Sales, EBIT/EV); `analyst_view` adds upside % and target dispersion; `earnings` adds
beat rate, surprise streak, average surprise and surprise consistency.

**Why.** Same thread as ADR-006/007: the inputs were already in hand and discarded. The balance
sheet was being loaded but only debt and cash were read — total assets and equity (needed for
gross profitability and ROIC) were one `_row` call away. Analyst targets and the earnings-surprise
history were returned raw, leaving the agent to recompute upside, dispersion and beat-streaks every
time. Doing it once in the data layer is correct, auditable and free.

**Choices that matter.**
- **No silent cap mismatch.** Market-cap-based ratios (FCF yield, EV multiples, earnings yield) are
  computed only on a *live* read (`as_of` is None). The source exposes only the *current* market
  cap; pairing it with a past statement on a point-in-time read would mix "today" with an old
  period, so those fields are deliberately null there. Statement-only ratios (net-debt/FCF, gross
  profitability, ROIC) are always available.
- **Positive-denominator guard.** Ratios where a negative denominator inverts the meaning
  (EV/EBIT with negative EBIT, debt/FCF with negative FCF, ROIC with negative invested capital) use
  a strict `>0` guard and return null otherwise — a missing number beats a misleading one.
- **EBIT ≈ operating income; ROIC is pretax.** Without D&A or the effective tax rate in the fetched
  set, EV/EBITDA and after-tax ROIC are not claimed (ADR-style honesty). EV/EBIT and pretax ROIC are
  the closest honest substitutes; the field names say so.
- **Measures, not a rating (ADR-004).** It reports a 97% ROIC and an 11% upside; it never says
  "high quality" or "buy".
- **Followed up (was M3b).** The extra balance/income/cash lines were later read (current
  assets/liabilities, retained earnings, D&A, interest expense), unlocking current_ratio,
  working_capital, debt_to_equity, EBITDA → EV/EBITDA & net_debt/EBITDA, interest_coverage and the
  **Altman Z″** distress score (book-equity variant, so no market cap needed → works on `as_of`).
  Beneish M-Score stays out — its 8 YoY indices need 5+ more line items with unstable spellings and
  it's a niche forensic score (see the manager desk's nice-to-have-probably-not note).

---

## ADR-009 — Derive crypto positioning/microstructure from data already fetched

**Decision.** `crypto_derivatives` adds a per-venue annualized funding rate and cross-venue
aggregates (OI-weighted funding consensus + annualized, funding dispersion, total OI in USD);
`crypto_order_book` adds order-book imbalance and microprice.

**Why.** The funding rate, per-venue open interest and the full top-of-book were already fetched
and handed over raw. A `0.00001` funding rate means nothing until annualized (~1%/yr); a trader
needs the *consensus* across venues, not three numbers to average by hand; and the order book
already carried the depth and sizes needed for imbalance and microprice. Same principle as
ADR-006/007/008 — compute once, in the data layer, measures not verdicts.

**Choices that matter.**
- **OI normalization was already solved.** Cross-venue funding must be weighted by open interest
  in a common unit, and venues report OI in different units (coin vs USD). The adapter already
  computes per-venue `open_interest_value` in USD, so the weighting and the total use that — no
  silent unit-mixing (the classic OI-aggregation bug).
- **8h funding interval, assumed and flagged.** A single `next_funding_time` snapshot cannot reveal
  whether a venue settles every 8h/4h/1h. Binance/Bybit/OKX default to 8h, so annualization uses
  3×/day and the `note` says so — an explicit assumption beats an unreliable guess from one stamp.
- **Microprice leans to the thin side.** `(bid·ask_size + ask·bid_size)/(bid_size+ask_size)` puts
  more weight on the side with *less* size, which is the better estimate of the next trade price
  than the plain mid — useful for execution and for reading short-horizon pressure alongside
  `imbalance`.
- **Partly followed up (M5b).** DVOL z-score & percentile vs a ~6-month window were added to
  `crypto_implied_vol` (the crypto analogue of the VIX regime read), self-contained from its own
  history. Still out: perp basis needs a spot price (cross-source tool-join for moderate value) and
  the long/short build-up needs ΔOI (two snapshots → breaks statelessness, ADR-003); order-book
  depth-impact is marginal given imbalance/microprice already ship and the snapshot is shallow.

---

## ADR-010 — Crypto cycle/tokenomics measures, and shipping null over faking

**Decision.** Add the **Mayer Multiple** (price / SMA-200) to `technicals`/`crypto_technicals` and
tokenomics ratios (float ratio, issuance progress, future dilution) to `crypto_asset_profile`.

**Why.** The Mayer Multiple is the canonical Bitcoin cycle gauge and both inputs (last price and
SMA-200) were already computed in `compute_technicals` — it was one division away. Supply ratios
turn raw circulating/total/max counts into a read on unlock overhang and issuance progress.

**Choices that matter.**
- **Null over faked.** The free Coinpaprika tier currently returns `circulating_supply` as null for
  some assets (BTC included), so the circulating-based ratios come back null. They are kept as-is —
  correct when the source provides the field, null (not a guessed substitute) when it doesn't.
  Falling back to total-supply would silently change the metric's meaning, so it isn't done; the
  caveat is documented instead. (M6b: source circulating supply elsewhere if this proves chronic.)
- **Uncapped assets.** Max-based ratios (issuance progress, future dilution) are null when there is
  no max supply (ETH and others) rather than dividing by zero.
- **Mayer is generic.** price/SMA-200 is reported for equities too (how far above/below the 200-day
  average); the bands (<0.8 accumulation, >2.4 euphoria) are BTC-calibrated, so the name documents
  intent while the number stays a plain measure (ADR-004).
- **Partly followed up (M6b).** SSR (total mcap ÷ Σ stablecoins) and stablecoin dominance were added
  to `crypto_macro` as a tool-layer join with the DefiLlama stablecoin total (the join is supplementary
  — a DefiLlama failure leaves the ratios null, never sinks the macro read). Still out, deliberately:
  Mcap/TVL per protocol (fragile token↔protocol name mapping), a circulating-supply fallback source
  (rework for one field), and on-chain valuation (MVRV/NVT/realized cap — needs node/Glassnode data the
  keyless sources don't provide). See the manager desk's nice-to-have-probably-not note.

---

## ADR-011 — Derive options signals from the chain already fetched; VRP as the stateless IV-rank

**Decision.** `options_volatility` adds, from the same option chain it already pulled, the IV skew
(OTM put vs call IV over ATM), put/call ratios (volume and open interest), and the volatility risk
premium (ATM IV minus trailing realized vol) with the IV/RV ratio.

**Why.** The full chain — every strike's IV, volume and open interest — was fetched and all but the
ATM IV discarded. Skew and put/call ratios were one pass over that frame; the VRP only needed the
realized vol, which the same adapter can compute from a short history pull (and which `analytics.py`
already implements from M1). These are the highest-value options reads, and computing them here
keeps the agent from re-deriving them.

**Choices that matter.**
- **VRP is the stateless IV-rank.** "Is IV rich or cheap right now?" is what traders want from IV
  rank/percentile — but those need a stored time series of the name's own IV, which a stateless
  server (ADR-003) can't keep. VRP and the IV/RV ratio answer the same question from a single read
  (today's IV vs the stock's own trailing realized vol), so they are shipped and IV-rank is
  explicitly omitted rather than faked with a cache.
- **Skip illiquid wings.** OTM strikes routinely report 0/NaN IV; the skew uses only the nearest OTM
  strike with IV > 0 on each side, so it isn't built on garbage quotes.
- **Black-Scholes stays possible without scipy.** The normal CDF (`math.erf`) is in the stdlib — so
  probability-of-ITM/touch is feasible later (M4b) — but it needs a target strike to be meaningful,
  so it's deferred rather than bolted on without a clear use.
- **Nearest-expiry caveat.** Like the existing expected move, the derived reads use the nearest
  expiry, which for very liquid names is often 0–1 DTE where skew is inherently noisy — the number is
  computed correctly; the noise is a property of that expiry, not a defect.
- **Measures, not a verdict (ADR-004).** It reports a VRP and a skew; it never says "sell premium".
- **Partly followed up (M4b).** IV term structure (slope + contango/backwardation) was added via one
  extra best-effort chain fetch at a longer expiry — a failure there (e.g. a 429) degrades to a null
  slope and never sinks the near read. Still out: earnings-driven IV crush and probability-of-ITM/
  touch (the latter needs a target strike to mean anything) — left until there's a clear use.

---

## ADR-012 — A failed source must never look like valid data

**Decision.** Standardize one failure signal across the adapters: a source that can't be reached
emits a machine-readable `unavailable: <reason>` (`rate_limited` / `timeout` / `error`) — via
`SourceUnavailable` on a raised path, a `status`/`source_status` field on a model, a `not_found`
vs `unavailable: …` split on per-symbol batch notes, or a `partial` flag when a sub-leg is dropped.
A throttle or timeout must surface as "couldn't fetch", never as a real reading (an all-null
snapshot, a `None`, an empty list, a thin-but-complete-looking result).

**Why.** This is the failure class that actually loses money for an autonomous loop: a 429 read as
"market cap = 0 / no news / unknown symbol" is a confident wrong input, not a visible gap. Honesty
over filling (the project constitution): the loop can retry or abstain on `unavailable`, but only if
it can tell that apart from a genuine `not_found`. It extends the pattern FRED/GDELT already had
(`MacroIndicator.status`, `WebNewsSearch.source_status`, `adapters/retry.py`) to the rest.

**Choices that matter.**
- **`crypto_macro` raises on a total 429** (both CoinGecko legs down) instead of returning an
  all-null `CryptoMacro` — matching its own docstring ("a 429 returns an honest error"); a single
  failed headline leg is flagged via `status` rather than dropped.
- **Retry only what's transient.** yfinance (sync) and CCXT now reuse `classify_transient`: 429/5xx/
  timeout are retried then raised as `SourceUnavailable`; a genuine 404/parse error is re-raised
  immediately (no retry storm) and stays an honest error.
- **One shared, rate-limited CCXT exchange per process** (markets loaded once) replaces the
  build-new-per-call pattern, so `enableRateLimit` throttles across a parallel manager fan-out
  instead of resetting its token bucket every call and drawing mass-429s. The instance is
  process-lifetime by design (warm pool); a failed first build isn't cached.
- **Live equity snapshot carries `quote_time` + `market_state`** so a stale weekend close ≠ a live
  tick (crypto already had `CryptoQuote.timestamp`).
- **`partial` over silent-thin.** `crypto_derivatives` / `treasury_data` / `world_macro` flag a
  dropped sub-leg rather than returning a complete-looking subset.
- **Safety = preventing failures, not limiting the user.** None of this blocks a deliberate choice;
  it only stops a data-source failure from masquerading as a fact.

## ADR-013 — Macro source expansion: net liquidity, financial conditions, claims, nowcasts, VIX term structure, dollar, energy

**Decision.** Broaden the FRED-backed `macro_context` from ~11 to ~34 series and add a matching set of
derived regime transforms: **Fed net liquidity** (WALCL − TGA − RRP, plus WoW and a ~1y weekly z-score),
**financial-conditions** tightness (NFCI > 0), the **jobless-claims** 4-week-average YoY, the **CFNAI-MA3
recession signal** (< −0.70), the **VIX term structure** (VXV/VIX, with a backwardation flag), **5y5y
forward inflation**, **M2 YoY**, a **broad-USD z-score**, and the **Brent−WTI** crude spread. New raw
levels (initial/continued claims, GDPNow, SOFR, nat-gas, copper, OVX/GVZ, STLFSI4, WEI…) surface
automatically in `indicators[]`; the `derived` block holds only transforms.

**Why.** The original macro read covered rates/curve/labour/inflation/VIX but missed the liquidity and
financial-conditions axis that drives risk assets between fundamentals prints. Net liquidity in
particular is a headline macro driver and is trivially keyless on FRED. All additions stay on the free,
no-key `fredgraph.csv` path — **no new API key, no `.env` change**.

**Choices that matter.**
- **Derived = transforms, never raw levels.** Raw series already appear in `indicators[]`; duplicating
  them in `derived` would be redundant. `derived` carries ratios/spreads/z-scores/YoY/boolean signals.
- **Net-liquidity unit alignment (the load-bearing gotcha).** WALCL and WTREGEN are in **$ millions**;
  RRPONTSYD is in **$ billions**. RRP is scaled **×1000** before subtracting, or the result is off by
  three orders of magnitude. The net series is built on WALCL's weekly dates, carrying the latest TGA/RRP
  forward to each date; a `notes` line records this mixed-frequency caveat.
- **Honesty over filling (ADR-012 / ADR-004 preserved).** Each field is null — never a fake number — when
  its series is missing or too short (≥2 weekly points for net-liquidity WoW, ≥8 for its z-score, ≥13
  monthly for M2 YoY, ≥53 weekly for claims YoY, ≥30 daily for the dollar z-score). Still measures, not a
  "risk-on" verdict.
- **Concurrent-fetch count rises ~11→~34.** Acceptable: fetches are concurrent (`asyncio.gather`), and a
  throttled/failed series degrades per-series via ADR-012 (`unavailable: …` status) instead of failing the
  call or vanishing.
- **Copper/gold ratio deliberately deferred.** FRED's gold fixing series were discontinued, so a
  copper-gold ratio belongs on the yfinance price path, not this FRED-only adapter. Copper level
  (`PCOPPUSDM`) is still surfaced raw.

## ADR-014 — Short interest folded into `ownership` (not a new tool)

**Decision.** Extend the existing `ownership` tool with a `short_interest` block instead of adding a
separate tool. It reads the figures yfinance already exposes on `Ticker(sym).info` — `sharesShort`,
`sharesShortPriorMonth`, `shortRatio` (days-to-cover), `shortPercentOfFloat`,
`sharesPercentSharesOut`, `dateShortInterest` — and derives `short_interest_change_pct`
(`(shares_short − prior_month)/prior_month × 100`, null when the prior is missing/zero).

**Why.** Short interest is the other half of "who is positioned in this stock", alongside the
13F/Form-4 holder data `ownership` already returns — a crowding/squeeze-risk read that belongs in
the same call, not a tool of its own. yfinance carries it for free on `.info`, so no new source/key.

**Choices that matter.**
- **Point-in-time, not live.** Short interest is exchange-reported ~twice a month with a lag, so the
  block is anchored to `short_interest_date` (the reported settlement date), never "today".
- **Best-effort, never breaks ownership (ADR-012 / honesty).** The `.info` read is a separate,
  slower, sometimes-missing fetch; it is wrapped in try/except and degrades to `short_interest=None`
  rather than failing the holder read. Every field is null when the source omits it — never
  fabricated — and the whole block is `None` (not an empty block) when no short field is present, so
  "no data" isn't mistaken for "zero short interest".

## ADR-015 — CFTC Commitments of Traders positioning (`cot_positioning`)

**Decision.** Add a keyless `cot_positioning` tool over the CFTC's public Socrata endpoint
(`publicreporting.cftc.gov/resource/jun7-fc8e.json`, the legacy futures-only report) — weekly
futures positioning split by trader class. Input: a `market` search string ("GOLD", "CRUDE OIL",
"E-MINI S&P", "EURO FX") and `weeks` (1..52, default 12). Returns the latest snapshot (speculator &
commercial long/short/net, open interest), derived `noncomm_net_pct_oi`, `noncomm_net_change`
(CFTC's own WoW delta), and `noncomm_net_zscore` (`zscore_of_last` over the window, null < 8 weeks),
plus a weekly `history`. This is the positioning dimension Scout otherwise lacks — `net` = long −
short shows whether speculators / commercials are crowded.

**Why.** No key, no auth, broad coverage (metals/energy/grains/FX/equity-index/rates in one
dataset). The legacy futures-only report (`jun7-fc8e`) was chosen over the disaggregated/TFF reports
for breadth and a stable schema. Positioning is orthogonal to the price/fundamentals/options data
already present and is a recognised contrarian-at-extremes input.

**Choices that matter.**
- **One request, client-side disambiguation.** A single date-ordered SoQL fetch (`upper(...) like
  '%QUERY%'`, generous capped limit) can match several markets (e.g. GOLD + MICRO GOLD). The primary
  series is the highest-latest-open-interest match; the others are listed in `matched_markets` and
  `note` so an ambiguous query is visible, never silently wrong.
- **Honesty over filling (ADR-012).** A 429/timeout surfaces as `source_status: unavailable: …`
  (via `with_retry`/`SourceUnavailable`) and an empty result; a genuine no-match returns an empty
  result WITH a `note` and no `source_status` — the two are distinguishable. The z-score is null
  below 8 weekly points; fields are null, never fabricated, when a record omits them.
- **Point-in-time.** Positions are as of the Tuesday, published the following Friday (~3-day lag);
  `as_of` is the report's settlement date, stated in `note`. Reuses `analytics.zscore_of_last`.

## ADR-016 — Coinbase/Binance spot premium (`coinbase_premium`)

**Decision.** Add a keyless `coinbase_premium` tool: the gap between US-spot (Coinbase, `<SYM>/USD`)
and offshore (Binance, `<SYM>/USDT`) price, `premium = (US-spot − offshore)/offshore × 100`.
Input: `symbol` (base asset, default "BTC"; "ETH" etc.), `days` (1..90, default 30). Returns the
latest `coinbase_price`/`binance_price`/`premium_pct`, a daily premium `history` (timestamp
intersection of both venues' `1d` OHLCV closes), and `premium_zscore` (`analytics.zscore_of_last`
over the series, null below 8 points). Positive premium = aggressive US/institutional buying (the
ETF bid tell); negative = US selling. Paywalled elsewhere (CryptoQuant); here it is arithmetic on
two prices Scout already fetches.

**Why.** It is the single best keyless read of US/institutional demand vs the offshore market, and
it is pure composition over existing CCXT spot data — no new source, no key. It is a positioning
tell, not a price, so it is verdict-free (ADR-004): the agent reads the sign/size and concludes.

**Choices that matter.**
- **Two venues, two shared exchanges (reuse, not bypass).** Composes TWO `CcxtMarketData`
  instances (coinbase/USD, binance/USDT), each keeping its own shared, rate-limited exchange (the
  Session-7 anti-429-fan-out instance) — never a fresh per-call ccxt object.
- **Honesty over filling (ADR-012).** A throttle/timeout on EITHER leg → `source_status:
  unavailable: <reason>` with a null premium (it cannot be computed honestly from one price), never
  a fabricated number. A symbol simply **not listed** on a venue (a ccxt `BadSymbol`, non-transient)
  is a distinct outcome: empty + a `note`, no `source_status` — so "venue doesn't carry it" is told
  apart from "couldn't fetch". The z-score is null below 8 daily points.
- **Binance is reachable from this machine** (verified live, not geo-blocked); live premium ≈ −0.14%.

## ADR-017 — Stablecoin peg deviation (`stablecoin_peg`)

**Decision.** Add a keyless `stablecoin_peg` tool: each major stablecoin's deviation from its $1
peg, read as `<SYM>/USD` spot on **Kraken** (which lists USDT, USDC and DAI vs USD). Input:
`symbols` (default `["USDT","USDC","DAI"]`) and an optional `venue` override (default kraken). Per
coin returns `price`, `deviation_bps = (price − 1) × 10000`, and a `depeg` flag set when
`|deviation_bps|` exceeds the module constant `_DEPEG_BPS_THRESHOLD = 50`. This is the PRICE axis of
stablecoin health — a depeg is a market-wide tail trigger.

**Why.** Scout already has `stablecoin_supply` (the SUPPLY axis, DefiLlama circulation); peg price
is the orthogonal, additive read it lacks. It is keyless CCXT spot — no new source. Raw basis-point
deviation + a flag, not a verdict (ADR-004).

**Choices that matter.**
- **Kraken default, reuse the shared exchange.** Reuses `CcxtMarketData` (with its shared,
  rate-limited exchange) via an injected factory; an optional `venue` override builds/caches a
  per-venue instance, still through the same machinery — never a bypass.
- **Honesty over filling (ADR-012).** A fetch failure (throttle/timeout) → `source_status:
  unavailable: <reason>`, so a missing price reads as "unavailable", not a real $0/peg. A symbol
  **not listed** on the venue (a ccxt `BadSymbol`, non-transient) is omitted from `items` with a
  `note` — distinct from a throttle. No magic number: the 50-bps depeg threshold is a named constant.

## ADR-018 — BTC base-layer fundamentals + fee market (`btc_network`)

**Decision.** Add a keyless `btc_network` tool composing TWO sources into one read of Bitcoin's
base layer. From **Blockchain.com Charts** (`api.blockchain.info/charts/{chart}`): hash rate, miner
revenue, on-chain transaction count, on-chain settlement USD volume and market cap. From
**mempool.space** (`/api/v1/fees/recommended`, `/api/v1/difficulty-adjustment`): the live sat/vB fee
tiers and the difficulty retarget. The valuation ratio **NVT is COMPUTED, not fetched**:
`nvt = market_cap / estimated_transaction_volume_usd`, plus a 90-day-smoothed `nvt_90d`
(`market_cap / 90-day average tx volume`, null under 90 daily points). A short `history` of hash
rate + NVT over the fetched window is returned for context.

**Why.** Scout had zero BTC base-layer fundamentals — the network-health / valuation dimension for
its single most important crypto asset. NVT is the canonical on-chain valuation ratio (the crypto
P/E analog); computing it from **on-chain settlement** volume (not exchange volume) makes it the
*real* NVT, which is otherwise paywalled. The live fee market is the congestion/cost read. Raw
measures, never a verdict (ADR-004).

**Choices that matter.**
- **New `btc_network` adapter dir, not folded into `onchain`.** `crypto_onchain` is a thin
  multi-chain metric list (BTC fees/hashrate, ETH gas); `btc_network` is a richer BTC-only
  composition with a derived ratio and a history. Kept separate so neither tool's contract bends.
- **Two independent legs, partial-tolerant (ADR-012).** Blockchain.com and mempool.space fail
  independently: if one is throttled the other still returns, the missing leg's fields stay **null**
  (never faked), and `partial=True` + `source_status: unavailable: <reason>` + `note` record the
  gap. Every network fetch is wrapped in `with_retry` so a 429/timeout backs off then surfaces an
  honest reason instead of a silent zero.
- **26-week fetch window.** Sized so the 90-day NVT average always has enough daily samples; the
  90-point floor is a named constant, and `nvt_90d` is null below it rather than computed on thin
  data.

## ADR-019 — DeFi protocol cash flow: fees vs revenue (`defi_fees`)

**Decision.** Extend the existing **DefiLlama** adapter (no new source dir) with a `defi_fees` tool.
Input: optional `protocol`. Without it → ecosystem overview: `total_fees_24h/7d`,
`total_revenue_24h`, and the top 15 protocols by 24h fees, each with category, chains, fees (24h/7d)
and revenue (24h) — fees joined to revenue **by protocol name** from a second `dataType=dailyRevenue`
overview call. With a `protocol` → that protocol's fees + revenue summary
(`/summary/fees/{slug}`). Endpoints used: `/overview/fees` (± `dataType=dailyRevenue`) and
`/summary/fees/{slug}`.

**Why.** Fees (what users pay) and revenue (what the protocol/token keeps) are the real **cash-flow
fundamentals** of a token — the DeFi analog of an income statement — which Scout's TVL/yield tools
don't capture. All keyless on DefiLlama's free tier.

**Choices that matter.**
- **Perps-DEX deliberately excluded.** The DefiLlama derivatives overview (`/overview/derivatives`)
  is Pro-gated (HTTP 402), so perps-DEX volume is out of free scope — documented in the tool
  docstring rather than half-supported.
- **Honesty over filling (ADR-012).** The fees overview is the headline: a 429/timeout on it →
  `source_status: unavailable: <reason>` (never an all-null body that reads as "no fees exist"). The
  revenue leg is supplementary — if it alone fails, fees still return with revenue **null** and a
  `note`, never zero. An unknown protocol (non-transient 404) returns empty with a `note`, distinct
  from a throttle. The top-N count and the retry policy are named constants/params.

## ADR-020 — FDA drug approvals + recalls (`fda_events`)

**Decision.** Add a keyless `fda_events` tool over **openFDA** (an optional free key only raises
rate limits — it is NOT required). One answer composes two independent endpoints: `/drug/drugsfda`
for approvals (an approval is a `submissions` entry with `submission_status == "AP"`, date in
`submission_status_date`; surface `application_number` + `products[].brand_name`) and
`/drug/enforcement` for recalls (`recalling_firm`, `report_date`, `product_description`,
`reason_for_recall`, `classification` = severity, `status`). Input: a sponsor/issuer `company` name
(e.g. from `company_dossier`) + `limit`. New `openfda` adapter dir, `FdaSource` port, `FdaEvents`
model.

**Why.** Approvals and recalls are the binary up/down catalysts that move pharma/biotech — a
dimension Scout's price/fundamentals/filings layers don't surface directly, and one of the few
FDA-authoritative feeds available with no key.

**Choices that matter.**
- **404 NOT_FOUND is an empty result, not a failure.** openFDA returns **HTTP 404 with
  `{"error":{"code":"NOT_FOUND"}}` when a query has ZERO matches**. The default fetch returns that
  body (instead of raising) so the adapter records it as an empty list + `note`; only a
  429/timeout/5xx is a genuine failure → `with_retry`/`SourceUnavailable` → `source_status:
  unavailable: …`. The two are distinguishable (ADR-012).
- **Two legs, independent + partial.** Approvals and recalls fail independently: a throttled leg sets
  a labelled `source_status` ("approvals unavailable: rate_limited") and returns empty while the
  other still returns. A genuine zero-match `note` is only emitted when BOTH legs returned cleanly
  and both were empty — a throttle never masquerades as "no events".
- **Name, not ticker.** Mapping a ticker to the exact sponsor-of-record string is fuzzy and out of
  scope; the caller passes the issuer/sponsor name and the docstring says so.

## ADR-021 — Clinical-trial pipeline (`clinical_trials`) — BUILT THEN WITHDRAWN (WAF-blocked)

**Decision.** A keyless `clinical_trials` tool over **ClinicalTrials.gov v2** was built (adapter,
port, models, tool, offline tests) and then **removed before shipping**. The v2 API is keyless and
the query is correct — but the host is behind a WAF that **blocks by client TLS fingerprint**, not
just User-Agent. Empirically: `curl` to `/api/v2/studies?...` returns **200** consistently, while the
same request from Python **httpx** (Scout's HTTP layer) returns **403 Forbidden** — with the default
UA, a `curl/*` UA, AND a full browser UA. Header spoofing does not move it; the block is on the TLS
ClientHello (JA3-style), which httpx/python-ssl can't change without a browser-impersonating stack.

**Why withdrawn.** Making it work would require `curl_cffi`/TLS-impersonation to defeat the WAF —
a fragile, cat-and-mouse, ToS-gray dependency that violates Scout's "free sources first, but not
fragile" bar (the same bar that keeps scraping sources like StockTwits/Farside out). Shipping a tool
that always 403s live would be dishonest — it reads as a feature but never returns data. So the clean
call is to NOT ship it rather than ship a WAF-evasion hack or a dead tool.

**Status.** Deferred. Revisit only if ClinicalTrials.gov drops the fingerprint WAF, or if a different
keyless biotech-pipeline source appears. `fda_events` (ADR-020) still covers FDA approval/recall
catalysts, which are the harder binary events anyway. Recorded here so nobody re-attempts the v2 API
blind and rediscovers the 403 the hard way.

## ADR-022 — Commodity bellwether ratios (`commodity_ratios`)

**Decision.** Add a keyless `commodity_ratios` tool computing **copper/gold** and **gold/silver**
from ~1y of daily futures closes (`HG=F`, `GC=F`, `SI=F`). Closes the copper-gold ratio deferred
from the macro wave. It adds **no new HTTP client**: it REUSES Scout's existing price path (the
yfinance `MarketDataSource`) via an injected `fetch_history` callable wired in the composition root.
For each ratio: latest value + a z-score (`zscore_of_last`, null under ~30 aligned points) + a daily
`history`, plus the three spot prices. New `commodities` adapter dir, `CommodityRatioSource` port,
`CommodityRatios`/`RatioPoint` models.

**Why.** copper/gold (Dr. Copper vs the safe haven) is a recognised risk-appetite tell and gold/silver
the classic precious-metals stress ratio — macro bellwethers Scout's per-symbol tools don't compose.
The LEVEL of copper/gold is arbitrary; the trend/z-score is the signal, so the tool ships the z-score.

**Choices that matter.**
- **Reuse the price path, not a new source.** Injecting `fetch_history(symbol) -> PriceHistory` keeps
  the futures quotes flowing through the one yfinance adapter already in the composition root and
  keeps tests fully offline (inject a synthetic `PriceHistory`).
- **Per-pair date alignment.** Each ratio is computed over the date **intersection** of its own two
  legs before dividing, so a stale/missing day never silently mismatches — and a missing third leg
  (e.g. silver) nulls only `gold_silver` with a `note`, leaving `copper_gold` intact.
- **Honesty over filling (ADR-012).** A leg whose fetch raises sets a labelled `source_status`
  ("copper unavailable: timeout"); a missing/empty leg nulls its ratio with a `note`; the z-score is
  null below 30 aligned points (and below non-zero variance). Bellwethers that MEASURE, never a
  verdict (ADR-004).
