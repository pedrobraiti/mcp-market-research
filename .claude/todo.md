# TODO

Plano vivo do projeto. Tarefas e subtarefas, marcadas conforme concluídas.

## Em progresso
- [ ] **Benchmark de pesquisa (decisão por evidência):** lado Claude Code já gerado (`benchmark/claude-code/`); aguardando o usuário rodar os 3 prompts no claude.ai web (`benchmark/PROMPTS-FOR-CLAUDE-WEB.md`) e salvar em `benchmark/claude-web/`. Depois eu comparo.

## Próximas
- [ ] `company_dossier(symbol, depth, as_of)` — meta-tool agregadora com `asyncio.gather` (já dá pra fazer com as 3 fontes atuais + crescer)
- [ ] Endurecer o adapter yfinance: cache leve + retry/backoff (rate limits), e provê **proveniência por campo** (de onde veio cada número)
- [ ] Próximas tools de aprofundamento por símbolo (v1/v2): `valuation_history`, `quality_metrics`, `technicals`, `price_history`
- [ ] Adapter SEC EDGAR (`filings`) — fonte primária/autoritativa p/ cruzar com yfinance (precisa `SCOUT_SEC_USER_AGENT`)
- [ ] Adapter FRED (`macro_context`)
- [ ] Tools de descoberta v1: `screen` (com critérios técnicos), `peers`, `compare`
- [ ] Tools de lote v1 (stateless): `watch_signals`, `news_digest`, `calendar`
- [ ] (Workstream da skill, NÃO do Scout) Skill de estratégia `/analyze` e `/invest` com os 2 modos + **camada de memória de tese** (escreve a tese; passa pro Scout verificar stateless)
- [ ] README: banner/logo no padrão do `mcp-ibkr-agent`

## Concluído
- [x] Setup inicial do projeto (`.claude/`, git, estrutura de memória)
- [x] Definir conceito e fronteira: MCP de dados ("Scout") separado do Valet, Claude Code como cérebro
- [x] Brainstorm multi-agente de tools/casos de uso (2 rodadas, 5 personas) → `docs/tool-brainstorm.md` + ADR dos 7 princípios de design
- [x] Scaffold do projeto espelhando o `mcp-ibkr-agent` (pyproject, hexagonal, CI, ruff/pytest, envelope `{ok,data}`)
- [x] Fatia vertical yfinance → `company_snapshot`/`fundamentals`/`dividends` com `as_of`, 17 testes offline + live-validado
- [x] Benchmark Claude Code (deep research) gerado: 3 relatórios em `benchmark/claude-code/`
