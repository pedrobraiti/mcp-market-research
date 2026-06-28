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
- **Deferred (M2b), not pretended.** Breakeven inflation (`T10YIE`), ex-ante real yield (`DFII10`)
  and the high-yield credit spread (`BAMLH0A0HYM2`) are high-value FRED series left for a follow-up
  — they are new raw inputs more than transforms of existing data.

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
- **Deferred (M3b).** Piotroski/Altman/Beneish and EV/EBITDA need inputs not yet fetched (current
  assets/liabilities, retained earnings, D&A, interest expense) — left for a follow-up rather than
  approximated past the point of meaning.

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
- **Deferred (M5b).** Perp basis needs a spot price (cross-source) and the long/short build-up read
  needs ΔOI (two snapshots in time) — the latter breaks statelessness (ADR-003), so both are left
  out rather than faked.
