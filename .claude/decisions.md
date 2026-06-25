# Decisões arquiteturais/técnicas

Registro de decisões com o "porquê". Append-only — não edita entradas antigas.

<!-- Formato:
## YYYY-MM-DD — Título curto da decisão
**Motivo:** por que foi decidido assim.
**Alternativas consideradas:** o que ficou de fora e por quê.
-->

## 2026-06-25 — Forma do projeto: MCP de dados, não programa standalone
**Motivo:** O objetivo é "muito nativo, com function calling, pra o Claude Code usar". Isso é a definição de um MCP server. O raciocínio/decisão fica com o Claude Code (o cérebro já existe); o projeto entrega os **sentidos** (dados) como tools. Um programa agêntico standalone reimplementaria, pior e pago (API), o loop de raciocínio que o Claude Code já dá nativo. Casa com a arquitetura e o espírito do `mcp-ibkr-agent`.
**Alternativas consideradas:** (a) programa Python autônomo dirigindo a API da Anthropic — rejeitado: exige API paga e é menos nativo; a autonomia/agendamento futura já existe no Claude Code (`/schedule`, `/loop`). (b) Juntar dados no mesmo repo do Valet — rejeitado: Valet é isolado e faz uma coisa; separar mantém a fronteira limpa.

## 2026-06-25 — Divisão de responsabilidades: dados = tools, julgamento = skill
**Motivo:** Coleta de dados, screeners, cálculo de indicadores, sizing, scoring e journaling de tese são determinísticos → viram **tools de MCP** (citáveis, sem alucinação). O julgamento ("essa empresa é um bom investimento dado tudo isso?") é o que se QUER que o LLM faça → fica na **skill de estratégia** (`/analyze`, `/invest`), não hardcoded.
**Alternativas consideradas:** Hardcodar a estratégia em código — rejeitado: engessa o que o agente faz melhor (ponderar) e vira manutenção infinita de regras.

## 2026-06-25 — Tools "gordas" e com propósito, paralelismo interno
**Motivo:** Expor poucas tools consolidadas (ex.: `company_dossier(symbol)`) em vez de dezenas de tools micro (`get_pe`, `get_revenue`…). A tool dispara internamente, em paralelo (`asyncio.gather`), várias fontes e devolve **um relatório estruturado**. Menos round-trips, menos contexto queimado, e é exatamente o "pesquisar várias informações simultaneamente" que o usuário pediu.
**Alternativas consideradas:** Muitas tools granulares — rejeitado: força o agente a orquestrar N chamadas e gasta contexto à toa.

## 2026-06-25 — Fontes de dados gratuitas primeiro, adapters plugáveis (hexagonal)
**Motivo:** Começar sem custo: yfinance (preço/fundamentos/técnicos), SEC EDGAR (filings oficiais), FRED (macro), stooq (histórico). Arquitetura hexagonal igual ao Valet: cada fonte é um adapter atrás de uma port, então trocar grátis→pago (Finnhub/FMP/Alpha Vantage) no futuro mexe só no adapter, sem tocar no domínio.
**Alternativas consideradas:** Já começar com API paga — rejeitado: o usuário não quer custo agora e as fontes grátis cobrem o essencial.

## 2026-06-25 — Universo limitado ao que a IBKR negocia (por ora)
**Motivo:** Não faz sentido coletar dados de ativos que o ecossistema não consegue executar. Foco em ações/ETFs dos EUA (o que o Valet alcança). O ecossistema maior terá outros MCPs de execução (Binance, corretora BR) — a camada de dados cresce quando esses chegarem.
**Alternativas consideradas:** Modelar multi-asset desde já (cripto, BR) — adiado: YAGNI até existir execução pra esses ativos.

## 2026-06-25 — Dois modos: confirmação (default público) vs autonomia (dono)
**Motivo:** Repo público → quem baixar deve ter, por **default**, o modo que **pede confirmação** antes de ordem live (seguro/previsível). O dono opera com **autonomia** ativada. O modo é orquestrado pela skill de estratégia (consome Valet+Scout), não por este MCP de dados, mas o projeto documenta e suporta ambos.
**Alternativas consideradas:** Só autonomia — rejeitado: perigoso como default público. Só confirmação — rejeitado: não atende o uso pessoal do dono.

## 2026-06-25 — Pesquisa narrativa (web) sem API paga; medir antes de confiar
**Motivo:** O grosso da precisão vem de **dado estruturado** (determinístico, grátis), não de web search. Para a parte narrativa (notícias/sentimento/teses), experimentar o `deep-research`/Workflow (subagentes) do Claude Code; fallback é o Claude entregar um prompt pronto pro usuário rodar no claude.ai web (que historicamente entregou relatórios superiores ao WebSearch cru). Decidir por **benchmark empírico**, não por promessa.
**Alternativas consideradas:** API da Anthropic com web search nativo — adiado: é paga. Automação de navegador dirigindo o claude.ai — rejeitado: frágil demais pra produção.
