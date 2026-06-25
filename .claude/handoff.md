# Handoff — de onde parei

> **Propósito:** este arquivo serve para que um chat NOVO saiba com precisão "de onde eu parei",
> de forma relativamente detalhada. É o PRIMEIRO arquivo que a próxima sessão lê.
> Mantenha-o vivo e específico — detalhado o bastante para retomar sem reconstruir o raciocínio.

**Última atualização:** 2026-06-25 — fim do setup inicial

## Onde parei
Acabei de rodar o `/setup` neste projeto novo (`mcp-market-research`, nome amigável **Scout**). Diretório estava vazio; criei toda a estrutura `.claude/`, `CLAUDE.md`, `README.md` esqueleto, `.gitignore`/`.gitattributes`/`.editorconfig`, `git init` e commit inicial. Repo será **público** no GitHub (`pedrobraiti/mcp-market-research`). Ainda **não há código Python** — só a fundação de memória/git e o conceito travado.

## Contexto mental
Este é o **segundo MCP** de um ecossistema de trading agêntico do usuário (Pedro). O primeiro, `mcp-ibkr-agent` ("Valet"), é a **execução** na Interactive Brokers — já existe, open source, validado live. Este aqui ("Scout") é o **data/info gathering**: os sentidos. O **cérebro é o próprio Claude Code** — ele raciocina e decide; a estratégia de decisão mora numa **skill** (`/analyze`, `/invest`), não em código. Por isso a forma é um **MCP server** (function calling nativo), não um programa standalone (que precisaria de API paga e reimplementaria o loop agêntico).

Princípios já decididos (ver `decisions.md`): tools **gordas e com propósito** (ex.: `company_dossier(symbol)` com `asyncio.gather` interno) em vez de dezenas de tools micro; **dados grátis primeiro** (yfinance, SEC EDGAR, FRED, stooq) atrás de **adapters plugáveis** (hexagonal, igual Valet); universo limitado ao **que a IBKR negocia** (ações/ETFs US) por ora; **dois modos** (confirmação por default pra público, autonomia pro dono) — orquestrados pela skill; pesquisa narrativa via `deep-research`/Workflow com fallback de prompt pro claude.ai web, **sem API paga**.

## Próximo passo concreto
**Desenhar a superfície de tools do MCP** — a lista de tools, suas assinaturas e o formato de retorno (envelope `{ok, data}` como no Valet). Mas antes, fechar com o usuário **3 decisões abertas** (abaixo), porque elas mudam o desenho das tools. Sem elas, dá pra começar o scaffold Python (pyproject, layout hexagonal, CI) que é decision-independent — mas o desenho das tools espera.

## Em aberto / armadilhas
Decisões que faltam o usuário fechar antes do desenho fino das tools:
1. **Profundidade/forma das tools** — confirmar a abordagem "poucas tools gordas" e quais dossiês fazem sentido (snapshot rápido vs dossiê completo vs comparação).
2. **Como nomear o nome amigável** — escolhi "Scout"; usuário pode trocar antes do push.
3. **Estilo de investimento alvo** — o usuário pediu "preparado pra TODOS os cenários e objetivos", então o dossiê precisa cobrir fundamentos+técnicos+macro+filings de forma genérica (não otimizar pra um estilo só). Isso amplia o escopo de dados — cuidar pra não virar over-engineering no MVP; entregar um **adapter vertical** (yfinance → snapshot) primeiro e crescer.

Armadilhas técnicas conhecidas (do Valet, valem aqui): rate limits de fontes grátis (yfinance/SEC têm limites); SEC EDGAR **exige header `User-Agent` identificável**; cuidar de cache pra não estourar limites; manter **zero segredo** versionado (repo público).

## Como retomar rápido
- Leia `context.md` (macro), `decisions.md` (porquês), este arquivo, e rode `git log --oneline -20`.
- Referência de padrão de qualidade/arquitetura: `C:\Users\ACS Gamer\Documents\vscode-local\agentic-trading` (o Valet) — espelhar layout hexagonal, envelope de retorno, estilo de README/ADR, CI (ruff+pytest).
- Comandos: ainda não há venv/código. Primeiro passo de build será `python -m venv .venv` + `pyproject.toml`.
