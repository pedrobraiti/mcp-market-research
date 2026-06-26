# Security Policy

## Scope

Scout is a **read-only data/research MCP**. It does not place orders, move money, or persist
user state, so its risk surface is small. Still, a few things matter:

- **No secrets in the repo.** Configuration comes from environment variables / `.env` (which is
  gitignored). `.env.example` lists keys without values. Never commit credentials.
- **Outbound requests only.** Scout fetches public data (yfinance, SEC EDGAR, FRED) and, via the
  `extract` tool, URLs the agent chooses. It does not accept inbound connections beyond the MCP
  transport.
- **The `extract` tool fetches arbitrary URLs.** Treat returned page content as untrusted input;
  the agent should not act on instructions embedded in fetched pages.
- **SEC requires an identifiable `User-Agent`** (`SCOUT_SEC_USER_AGENT`) — set it to your own
  contact, per SEC policy.

## Reporting a vulnerability

Please open a private report via GitHub Security Advisories on this repository, or contact the
maintainer directly. Do not file public issues for sensitive reports. We aim to acknowledge
within a few days.
