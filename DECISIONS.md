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
