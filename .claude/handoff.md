# Handoff — de onde parei

> **Propósito:** este arquivo serve para que um chat NOVO saiba com precisão "de onde eu parei",
> de forma relativamente detalhada. É o PRIMEIRO arquivo que a próxima sessão lê.
> Mantenha-o vivo e específico — detalhado o bastante para retomar sem reconstruir o raciocínio.

**Última atualização:** 2026-06-25 — fim do brainstorm multi-agente de tools

## Onde parei
Setup feito e repo público no ar (`pedrobraiti/mcp-market-research`, nome amigável **Scout**). Em seguida conduzi um **brainstorm multi-agente** (5 subagentes sob personas de usuário, 2 rodadas: ideação + debate cruzado em que eles "conversaram"). Resultado consolidado em **`docs/tool-brainstorm.md`** e os 7 princípios de design viraram ADR em `decisions.md`. Entreguei o digest ao usuário e estou **aguardando 4 decisões abertas** dele (ver fim de `docs/tool-brainstorm.md`) antes de travar o corte v1 das tools. Ainda **não há código Python**.

## Resultado-chave do brainstorm (não reabrir sem motivo)
O debate convergiu forte. Constituição do Scout (7 princípios, no ADR): **stateless por design**; **`as_of` point-in-time em toda tool** (dissolve a necessidade de estado); **tool calcula, não conclui** (dado + régua, nunca veredito); **camada de evidência com proveniência** (não curadoria opinativa); **lote só quando a saída é agregada**; **meta-tools gordas só agregam, não recomendam**; **nomes sem vocabulário de execução**. Decisão grande: **memória de tese/watchlist/alertas SAI do Scout → mora na skill de estratégia**; o Scout só verifica stateless (recebe a tese + a data como argumento). Superfície dividida em v1 (~12 tools núcleo) e v2; lista completa na tabela de `docs/tool-brainstorm.md`.

## Contexto mental
Este é o **segundo MCP** de um ecossistema de trading agêntico do usuário (Pedro). O primeiro, `mcp-ibkr-agent` ("Valet"), é a **execução** na Interactive Brokers — já existe, open source, validado live. Este aqui ("Scout") é o **data/info gathering**: os sentidos. O **cérebro é o próprio Claude Code** — ele raciocina e decide; a estratégia de decisão mora numa **skill** (`/analyze`, `/invest`), não em código. Por isso a forma é um **MCP server** (function calling nativo), não um programa standalone (que precisaria de API paga e reimplementaria o loop agêntico).

Princípios já decididos (ver `decisions.md`): tools **gordas e com propósito** (ex.: `company_dossier(symbol)` com `asyncio.gather` interno) em vez de dezenas de tools micro; **dados grátis primeiro** (yfinance, SEC EDGAR, FRED, stooq) atrás de **adapters plugáveis** (hexagonal, igual Valet); universo limitado ao **que a IBKR negocia** (ações/ETFs US) por ora; **dois modos** (confirmação por default pra público, autonomia pro dono) — orquestrados pela skill; pesquisa narrativa via `deep-research`/Workflow com fallback de prompt pro claude.ai web, **sem API paga**.

## Próximo passo concreto
Aguardar as **4 decisões abertas** do usuário (§Decisões abertas em `docs/tool-brainstorm.md`): (1) memória de tese na skill e não no Scout; (2) travar corte v1; (3) `as_of` em todas as assinaturas; (4) narrativa/web. Assim que ele responder, **travar a superfície v1** e começar o scaffold + a fatia vertical (yfinance → `company_snapshot`/`fundamentals`/`dividends`, que é independente das decisões e pode até começar antes).

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
