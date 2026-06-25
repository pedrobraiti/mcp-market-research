# TODO

Plano vivo do projeto. Tarefas e subtarefas, marcadas conforme concluídas.

## Em progresso
- [ ] **Decisões abertas com o usuário** (bloqueiam o corte final do v1) — ver `docs/tool-brainstorm.md` §Decisões abertas: (1) memória de tese mora na skill, não no Scout? (2) travar corte v1 (~12 tools); (3) `as_of` em todas as assinaturas; (4) narrativa/web.

## Próximas (pós-decisão)
- [ ] Travar a superfície v1 a partir do `docs/tool-brainstorm.md` (assinaturas + envelope `{ok, data}` + `as_of` opcional)
- [ ] Decidir stack base: FastMCP + libs de dados (yfinance, sec-edgar/`requests`, fredapi/`requests`)
- [ ] Scaffold Python: `pyproject.toml`, venv, layout hexagonal (`domain/`, `adapters/`, `server/`), CI (ruff+pytest) espelhando o `mcp-ibkr-agent`
- [ ] Definir `domain/` — models e ports (MarketDataSource, FilingsSource, MacroSource…), com `as_of` no contrato
- [ ] **Fatia vertical** (independente das decisões): yfinance → `company_snapshot`, `fundamentals`, `dividends` (dado puro, v1 unânime), com testes
- [ ] Tool consolidada `company_dossier(symbol, depth, as_of)` com paralelismo interno (`asyncio.gather`)
- [ ] Adapter SEC EDGAR (`filings`) e adapter FRED (`macro_context`)
- [ ] Tools de descoberta v1: `screen` (com critérios técnicos), `peers`, `compare`
- [ ] Tools de lote v1 (stateless): `watch_signals`, `news_digest`, `calendar`
- [ ] Camada narrativa: `deep-research`/Workflow + fallback de prompt pro claude.ai web (decidir por benchmark)
- [ ] (Workstream da skill, NÃO do Scout) Skill de estratégia `/analyze` e `/invest` com os 2 modos + **camada de memória de tese** (escreve a tese; passa pro Scout verificar stateless)
- [ ] README profissional em inglês + banner, no padrão do `mcp-ibkr-agent`

## Concluído
- [x] Setup inicial do projeto (`.claude/`, git, estrutura de memória)
- [x] Definir conceito e fronteira: MCP de dados ("Scout") separado do Valet, Claude Code como cérebro
- [x] Brainstorm multi-agente de tools/casos de uso (2 rodadas, 5 personas) → `docs/tool-brainstorm.md` + ADR dos 7 princípios de design
