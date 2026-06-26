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

## 2026-06-25 — Princípios de design das tools (brainstorm multi-agente)
**Motivo:** Brainstorm com 5 subagentes (personas de usuário) em 2 rodadas (ideação + debate cruzado) convergiu numa "constituição" do Scout. Detalhe completo em `docs/tool-brainstorm.md`.
- **P1 — Stateless por design.** Memória de tese/watchlist/alertas = estado de decisão do usuário → mora na **skill/camada de memória**, NUNCA no Scout. MCP de dados ser stateless é feature (mesma pergunta → mesmo mundo, sem 2ª fonte de verdade competindo com a skill).
- **P2 — `as_of` (point-in-time) em toda tool de research.** Comparação temporal ("entrada vs. agora") vira composição de 2 leituras stateless; dissolve a necessidade de estado. A skill guarda a data; o Scout só lê o snapshot. Assinaturas nascem com `as_of` opcional.
- **P3 — A tool CALCULA, não CONCLUI.** Dado + régua explícita, nunca veredito embutido. Limiares vêm do caller (ou Scout devolve valor cru + régua). Mantém tudo como sentido, não julgamento.
- **P4 — Camada de evidência com proveniência, não curadoria opinativa.** Tools temáticas/macro entregam associações verificáveis + sensibilidades estatísticas com a evidência anexa; a IA conclui. Output não-auditável = opinião = não é Scout.
- **P5 — Lote first-class só quando a saída é agregada/filtrada** (correlação, digest, "só o que acendeu"). "Mesmo dado N vezes" fica por-símbolo. Scanner market-first (recebe escopo) ≠ batch-of-symbols (recebe lista).
- **P6 — Meta-tools gordas OK enquanto só agregam dados** (dossier, risk_readout). Linha vermelha: descrever risco sim, recomendar ação/sizing não.
- **P7 — Nomenclatura sem vocabulário de execução.** `pre_trade_brief`→`risk_readout`; `position_diff`→`changes_since`; detecção stateless usa sufixo `_check`, nunca `_watch`.
**Alternativas consideradas:** Memória de tese DENTRO do Scout (defendida na rodada 1 pelo fluxo-conjunto) — rejeitada no debate: vira 2ª fonte de verdade stateful e invade a skill. Tools com veredito embutido (valuation_estimate→"preço justo", thesis_review→"saia", macro_to_sectors→"quem ganha") — rejeitadas/reformuladas: terceirizam o julgamento da IA pra dentro da tool.

## 2026-06-25 — Camada de pesquisa: research mora no cérebro; Scout só dá o sentido `extract`
**Motivo:** Benchmark cego (3 temas, ver `benchmark/RESULTS.md`) comparou a pesquisa do Claude Code (agentes+WebSearch) com a claude.ai web. Resultado: web venceu os 3 mas por margem modesta (84% vs 96%), e o Claude Code **convergiu em todos os fatos centrais** (eventos reais de jun/2026, não alucinação). "Fazer deep research" decompõe em 4 passos: decidir o que pesquisar (cérebro) → buscar (sentido) → extrair conteúdo (sentido) → ler/cruzar/concluir (cérebro). Logo o PROCESSO de deep research é do cérebro (skill/subagentes), não do Scout — uma tool `deep_research(tema)→relatório` faria síntese/juízo dentro dela, cruzando a linha (viola "a tool calcula, não conclui"). Os gaps do benchmark caem em lados diferentes: (a) **sourcing primário** — a web venceu porque buscou 8-Ks/10-Ks da SEC que nossos agentes não conseguiram (403/anti-bot) → é problema de CAPTURA, fechável com uma tool `extract(url)` no Scout (fetch com headers → markdown limpo) + o adapter SEC já existente; (b) **caveats/cenários** — é problema de PROMPT/skill (cérebro), não de dado.
**Decisão:** (1) A pesquisa narrativa mora no **cérebro** (skill de deep research / subagentes do Claude Code), que já está essencialmente no mesmo nível da claude web. (2) O Scout NÃO terá tool de deep research que conclui; terá o **sentido `extract(url)/fetch_clean(urls[])`** (captura pura: URL→markdown limpo, token-efficient) como apoio à pesquisa do cérebro. (3) `web_search` próprio é opcional/baixa prioridade (redundante com o WebSearch nativo). (4) "Mandar prompt pra claude.ai web" vira escape hatch opcional, não mecanismo central.
**Alternativas consideradas:** Tool `deep_research` no Scout — rejeitada (cruza a fronteira sentido/cérebro). Depender de copiar/colar pra claude web como mecanismo central — rejeitada (gap é modesto e fechável do nosso lado). Construir `web_search` próprio já — adiado (redundante com o nativo; `extract` agrega mais).
