# Contributing to Scout

Thanks for your interest! Scout is a **stateless data/research MCP** — the "senses" layer of an
agentic-trading stack. Contributions are welcome; please keep them aligned with the project's
design principles (see [DECISIONS.md](DECISIONS.md)).

## Ground rules

- **Tools return data, never a verdict.** No "is this a buy?", no embedded "fair price". Provide
  the numbers and an explicit ruler; the calling agent concludes.
- **Stateless.** No persisted user state. Reads take an optional `as_of` and otherwise return
  the latest world.
- **One adapter per source, behind a port.** Add new data sources as adapters that satisfy a
  domain port; keep the domain free of vendor details.
- **Free sources first.** Prefer keyless/free data; a paid provider should be optional and
  pluggable behind the same port.

## Setup

```bash
python -m venv .venv
pip install -e ".[dev]"
pytest -q          # tests must pass
ruff check .       # lint must be clean
```

## Adding a tool

1. Add/extend a model in `domain/models.py` and a port method in `domain/ports.py`.
2. Implement it in an adapter under `adapters/`. Make the network/library call **injectable**
   (a factory or `fetch_*` callable) so it can be unit-tested fully offline.
3. Expose it in `server/app.py` as an `@mcp.tool()` returning the `{"ok", "data"}` envelope,
   with a clear docstring (the agent reads it).
4. Add offline tests; live-validate manually before opening a PR.

## Commits & PRs

- Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`…).
- Keep PRs focused. Describe what the tool returns and how you validated it.
- New env vars: document them in `.env.example`.
