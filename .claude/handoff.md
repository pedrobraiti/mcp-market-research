# Handoff — de onde parei

> **Propósito:** este arquivo serve para que um chat NOVO saiba com precisão "de onde eu parei",
> de forma relativamente detalhada. É o PRIMEIRO arquivo que a próxima sessão lê.
> Mantenha-o vivo e específico — detalhado o bastante para retomar sem reconstruir o raciocínio.

**Última atualização:** 2026-06-25 — benchmark de pesquisa concluído + decisão da camada de research

## Onde parei
O projeto **Scout** (`mcp-market-research`, público em `pedrobraiti/mcp-market-research`) tem **código rodando**: scaffold espelhando o `mcp-ibkr-agent` (Valet) + **5 tools**, com **33 testes offline** passando, ruff limpo e **validado ao vivo** (yfinance: AAPL/MSFT; SEC EDGAR: 10-Ks reais da AAPL). Rodei o **lado Claude Code do benchmark** (3 relatórios em `benchmark/claude-code/`).

**Benchmark concluído.** Usuário trouxe os 3 relatórios da claude.ai web; 3 juízes cegos compararam. Resultado em `benchmark/RESULTS.md`: claude web venceu os 3 mas por margem modesta (84% vs 96%) e o Claude Code **convergiu em todos os fatos centrais** (eventos reais, não alucinação). **Decisão registrada (ADR 2026-06-25):** a pesquisa narrativa mora no **cérebro** (skill/subagentes do Claude Code, que já está no mesmo nível); o Scout NÃO terá tool de deep-research que conclui — ganhará só o **sentido `extract(url)`** (URL→markdown limpo) pra fechar o gap de sourcing primário (a web venceu em parte porque buscou 8-Ks da SEC que nossos agentes levaram 403). Copiar/colar pra claude web = escape hatch opcional.

**Aguardando o usuário** escolher a próxima prioridade de código (ele perguntou sobre a fronteira research=tool vs cérebro — já respondida com o benchmark). Opções no `todo.md`: SEC fase 2 (XBRL cross-check), `extract` (sentido de pesquisa), `price_history`/`technicals`, FRED.

## O que já está implementado (não refazer)
- `src/scout/` layout hexagonal: `config.py` (pydantic-settings, prefixo `SCOUT_`), `domain/models.py` (CompanySnapshot, Fundamentals, DividendHistory, CompanyDossier, Filing/FilingsList — Decimal, com `as_of`), `domain/ports.py` (`MarketDataSource` e `FilingsSource`, com `as_of`), `adapters/yfinance/market_data.py` (parsing defensivo, `asyncio.to_thread`, import lazy, factory injetável, **retry/backoff**), `adapters/sec/edgar.py` (resolução de CIK via `company_tickers.json` cacheada, submissions API, `fetch_json` injetável, UA da SEC), `research/dossier.py` (`build_dossier`, `asyncio.gather`, tolerante a falha → `notes`), `server/services.py` (compõe yfinance + SEC) e `server/app.py` (FastMCP, envelope `{ok,data}`, **5 tools**). `healthcheck.py`.
- Tools: `company_dossier(depth)`, `company_snapshot`, `fundamentals(period)`, `dividends`, `filings(form_type, limit)` — todas com `as_of` opcional (ISO). `filings` exige `SCOUT_SEC_USER_AGENT`.
- Decisões de design aplicadas: stateless, `as_of`, dado puro (sem veredito), valores derivados quantizados, streak/cut só por anos consecutivos, retry deixa falha transitória de se disfarçar de "símbolo inexistente".
- CI em `.github/workflows/ci.yml` (ruff+pytest, branch `master`).

## Próximo passo concreto
Quando o usuário trouxer os relatórios do claude.ai web: comparar os 3 pares (profundidade, precisão, fontes, tratamento de incerteza) e registrar a conclusão (decide a camada narrativa). Se quiser avançar código antes disso: cache TTL + proveniência por campo no yfinance; refinar `had_cut`/streak (dividendos especiais/timing); ou próximas tools por símbolo (`valuation_history`, `quality_metrics`, `technicals`). Ver `todo.md`.

## Em aberto / armadilhas
- **Limitações do yfinance (ponto levantado pelo usuário):** é scraper não-oficial do Yahoo — pode quebrar quando o Yahoo muda, tem rate limit, `.info` é pesado e às vezes incompleto, e fundamentos históricos/point-in-time são limitados. Plano (não é "trocar", é "complementar"): manter yfinance como fonte default mas, sendo hexagonal, **cruzar com SEC EDGAR** (fundamentos autoritativos), **FRED** (macro) e **stooq** (preço fallback), e expor **proveniência por campo**. O `as_of` já nasce no contrato mas hoje só é honrado de fato para preço (history) e dividendos (filtro); fundamentos point-in-time dependem do que a fonte dá.
- **Nuance dividendos:** `had_cut` pode dar True por timing de pagamentos (anos com 4 vs 5 ex-dates) mesmo sem corte real do valor por ação — documentar/refinar depois (contar trailing-4 ou taxa por ação).
- **Benchmark macro:** o relatório de macro do agente construiu um cenário 2026 bastante específico/especulativo (choque geopolítico) — pesquisa sobre futuro/recente pode alucinar; avaliar como cada lado lida com incerteza É parte do teste.

## Como retomar rápido
- `& ".venv\Scripts\python.exe" -m pytest -q` (17 testes), `ruff check .`, `python -m scout.healthcheck AAPL`.
- Referência de padrão: `C:\Users\ACS Gamer\Documents\vscode-local\agentic-trading` (Valet).
- Superfície de tools planejada + princípios: `docs/tool-brainstorm.md` e ADR em `.claude/decisions.md` (2026-06-25).
