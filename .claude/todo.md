# TODO

Plano vivo do projeto. Tarefas e subtarefas, marcadas conforme concluídas.

## Em progresso
- [ ] Desenhar a superfície de tools do MCP (lista, assinaturas, formato de retorno) — **depende de decisões abertas** (ver `handoff.md`)

## Próximas
- [ ] Decidir stack base: FastMCP + libs de dados (yfinance, sec-edgar/`requests`, fredapi/`requests`)
- [ ] Scaffold Python: `pyproject.toml`, venv, layout hexagonal (`domain/`, `adapters/`, `server/`), CI (ruff+pytest) espelhando o padrão do `mcp-ibkr-agent`
- [ ] Definir `domain/` — models (Dossier, Fundamentals, Technicals, Filing, MacroSnapshot…) e ports (MarketDataSource, FilingsSource, MacroSource…)
- [ ] Primeiro adapter vertical de ponta a ponta: yfinance → `company_snapshot(symbol)` (preço + fundamentos básicos), com testes
- [ ] Tool consolidada `company_dossier(symbol, depth)` com paralelismo interno (`asyncio.gather`)
- [ ] Adapter SEC EDGAR (filings 10-K/10-Q/8-K) e tool `filings(symbol, type)`
- [ ] Adapter FRED (macro) e tool `macro_context()`
- [ ] Camada narrativa: tool/skill de research que usa `deep-research`/Workflow + fallback de prompt pro claude.ai web
- [ ] Skill de estratégia `/analyze` (só pesquisa) e `/invest` (pesquisa→decide→executa via Valet), com os dois modos (confirmação/autonomia)
- [ ] Memória de tese: registrar a tese na compra, revisitar na venda (journaling auditável)
- [ ] README profissional em inglês + banner, no padrão do `mcp-ibkr-agent`

## Concluído
- [x] Setup inicial do projeto (`.claude/`, git, estrutura de memória)
- [x] Definir conceito e fronteira: MCP de dados ("Scout") separado do Valet, Claude Code como cérebro
