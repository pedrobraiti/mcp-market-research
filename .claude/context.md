# Contexto do projeto

> Camada **estável** da memória: o que o projeto é e suas características macro. Muda devagar.
> O detalhe volátil de "de onde parei" fica no `handoff.md`; as tarefas, no `todo.md`;
> as decisões com o porquê, no `decisions.md`.

**Nome:** mcp-market-research (nome amigável: **Scout**)
**Descrição:** Servidor MCP de **coleta e análise de dados financeiros** para agentes de IA — a camada de "sentidos" que embasa decisões de investimento. Par do `mcp-ibkr-agent` (Valet, execução): Valet são as mãos, Scout são os sentidos, o Claude Code é o cérebro.
**Stack:** Python 3.12+, MCP server (FastMCP), arquitetura hexagonal (ports & adapters) sobre fontes de dados financeiras **gratuitas** (yfinance, SEC EDGAR, FRED) plugáveis. Docs em inglês (repo público).

## Visão geral
Este projeto é o segundo MCP de um ecossistema maior de trading agêntico. O `mcp-ibkr-agent` já entrega a **execução** confiável na Interactive Brokers; este MCP entrega o **data/info gathering**: cotações, fundamentos, técnicos, filings SEC, contexto macro e notícias — em tools "gordas" e com propósito, com paralelismo interno (`asyncio`), pra que o agente pesquise muitas dimensões de uma empresa em uma única chamada. Quem **raciocina e decide** o que/quando investir é o Claude Code, guiado por uma skill de estratégia (`/analyze`, `/invest`). O projeto não constrói "uma IA" — constrói os órgãos sensoriais de uma IA que já existe.

Escopo de universo: por enquanto, **o que a IBKR alcança** (ações/ETFs majoritariamente dos EUA). Foco em mercado de fora (gringa), vendável a brasileiros. Futuro: outros MCPs de execução (Binance, corretora BR) podem se somar ao ecossistema; a camada de dados pode crescer junto.

## Fase atual
Setup inicial — arquitetura conceitual travada (MCP de dados + skills de estratégia, Claude Code como cérebro). Próximo: desenhar a superfície de tools e o primeiro adapter de dados.

## Restrições e bloqueios de longo prazo
- **Sem API paga** para começar — só fontes gratuitas (yfinance, SEC EDGAR, FRED, stooq). Free tiers pagos (Finnhub/FMP/Alpha Vantage) só depois, se faltar dado. Cada fonte é um **adapter plugável** (trocar grátis→pago mexe só no adapter).
- **Universo limitado ao que a IBKR negocia** (por ora). Não modelar ativos que o ecossistema não consegue executar.
- **Dois modos de operação** (decisão de produto): por **default**, modo que pede **confirmação** antes de ordem (pra quem baixar do GitHub); o dono roda em modo **autonomia** ativada. O modo é da skill de estratégia, não deste MCP de dados — mas o projeto deve documentar/suportar ambos.
- **Repo PÚBLICO** → zero segredo versionado (`.env` no gitignore, `.env.example` espelhado sem valores). Docs em inglês.
- **Pesquisa narrativa (web)** não usa API paga: experimentar `deep-research`/Workflow (subagentes) do Claude Code; fallback é o Claude entregar um prompt pronto pro usuário rodar no claude.ai web. Dado estruturado (determinístico) é o grosso do valor; narrativa é a minoria.
