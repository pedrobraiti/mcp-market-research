# Handoff — de onde parei

> **Propósito:** este arquivo serve para que um chat NOVO saiba com precisão "de onde eu parei",
> de forma relativamente detalhada. É o PRIMEIRO arquivo que a próxima sessão lê.
> Mantenha-o vivo e específico — detalhado o bastante para retomar sem reconstruir o raciocínio.

**Última atualização:** 2026-06-25 — fatia vertical pronta + benchmark gerado

## Onde parei
O projeto **Scout** (`mcp-market-research`, público em `pedrobraiti/mcp-market-research`) saiu do papel. Já existe **código rodando**: scaffold completo espelhando o `mcp-ibkr-agent` (Valet) + a primeira **fatia vertical** funcionando (yfinance → 3 tools), com 17 testes offline passando, ruff limpo e **validado ao vivo** (`scout.healthcheck AAPL` retorna preço/PE/dividendos reais). Também rodei o **lado Claude Code do benchmark** de pesquisa (3 relatórios em `benchmark/claude-code/`).

**Aguardando o usuário** rodar os 3 prompts do `benchmark/PROMPTS-FOR-CLAUDE-WEB.md` no claude.ai web e salvar em `benchmark/claude-web/` — aí eu comparo os dois lados e decidimos a camada narrativa.

## O que já está implementado (não refazer)
- `src/scout/` layout hexagonal: `config.py` (pydantic-settings, prefixo `SCOUT_`), `domain/models.py` (CompanySnapshot, Fundamentals, DividendHistory — Decimal, com `as_of`), `domain/ports.py` (`MarketDataSource`, métodos com `as_of`), `adapters/yfinance/market_data.py` (parsing defensivo, `asyncio.to_thread`, import lazy do yfinance, factory injetável p/ testes offline), `server/services.py` (composição) e `server/app.py` (FastMCP, envelope `{ok,data}`, 3 tools). `healthcheck.py` (smoke test ao vivo).
- Tools: `company_snapshot`, `fundamentals(period)`, `dividends` — todas com `as_of` opcional (ISO).
- Decisões de design aplicadas: stateless, `as_of`, dado puro (sem veredito), valores derivados quantizados, streak/cut só por anos consecutivos (corrigido o bug que inflava streak atravessando o buraco de dividendos da Apple 1996–2012).
- CI em `.github/workflows/ci.yml` (ruff+pytest, branch `master`).

## Próximo passo concreto
Quando o usuário trouxer os relatórios do claude.ai web: comparar os 3 pares (profundidade, precisão, fontes, tratamento de incerteza) e registrar a conclusão (decide a camada narrativa). Em paralelo / se quiser avançar código: `company_dossier` (agrega as 3 tools via `asyncio.gather`) e endurecer o yfinance (cache + retry/backoff + proveniência por campo). Ver `todo.md`.

## Em aberto / armadilhas
- **Limitações do yfinance (ponto levantado pelo usuário):** é scraper não-oficial do Yahoo — pode quebrar quando o Yahoo muda, tem rate limit, `.info` é pesado e às vezes incompleto, e fundamentos históricos/point-in-time são limitados. Plano (não é "trocar", é "complementar"): manter yfinance como fonte default mas, sendo hexagonal, **cruzar com SEC EDGAR** (fundamentos autoritativos), **FRED** (macro) e **stooq** (preço fallback), e expor **proveniência por campo**. O `as_of` já nasce no contrato mas hoje só é honrado de fato para preço (history) e dividendos (filtro); fundamentos point-in-time dependem do que a fonte dá.
- **Nuance dividendos:** `had_cut` pode dar True por timing de pagamentos (anos com 4 vs 5 ex-dates) mesmo sem corte real do valor por ação — documentar/refinar depois (contar trailing-4 ou taxa por ação).
- **Benchmark macro:** o relatório de macro do agente construiu um cenário 2026 bastante específico/especulativo (choque geopolítico) — pesquisa sobre futuro/recente pode alucinar; avaliar como cada lado lida com incerteza É parte do teste.

## Como retomar rápido
- `& ".venv\Scripts\python.exe" -m pytest -q` (17 testes), `ruff check .`, `python -m scout.healthcheck AAPL`.
- Referência de padrão: `C:\Users\ACS Gamer\Documents\vscode-local\agentic-trading` (Valet).
- Superfície de tools planejada + princípios: `docs/tool-brainstorm.md` e ADR em `.claude/decisions.md` (2026-06-25).
