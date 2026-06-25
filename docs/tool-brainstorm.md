# Scout — Brainstorm de tools e casos de uso (rodada multi-agente)

> Relatório do brainstorm conduzido com 5 subagentes sob personas distintas de usuário,
> em duas rodadas: (1) ideação divergente em paralelo; (2) "conversa" cruzada — cada
> agente recebeu o consolidado dos outros + 4 tensões de design e reagiu/convergiu.
> Conceitual de propósito: identifica a NECESSIDADE de dado, não o COMO obter.
> Data: 2026-06-25.

## Personas usadas
1. **Fundamentalista / value / DCA** — valuation, moat, dividendos, preço justo.
2. **Trader ativo / swing / momentum** — técnicos, catalisadores, força relativa, volatilidade, intraday.
3. **Monitoramento & risco de portfólio** — acompanhar posições já abertas, alertas, exposição, correlação.
4. **Temático / macro / descoberta (top-down)** — tese → nomes, setores, rotação, drivers macro.
5. **Simulador do fluxo conjunto (Scout + Valet)** — loop completo idea→DD→executa→monitora→sai, p/ achar gaps que só aparecem no uso real.

---

## Princípios de design que emergiram do debate

Estes são o resultado mais valioso do exercício — viraram a "constituição" do Scout.

### P1 — Scout é STATELESS por design (feature, não limitação)
Mesma pergunta → mesmo mundo, sem efeito colateral, sem "verdade própria" a sincronizar. Memória de tese, watchlist e alertas são **estado de decisão do usuário**, não dado de mercado → moram na **skill de estratégia / numa camada de memória à parte**, nunca dentro do Scout. Consenso final unânime (até trader e fluxo-conjunto, que defendiam estado, concederam). O Valet já é a fonte de verdade do estado de execução; criar uma segunda fonte stateful no Scout seria o mesmo tipo de acoplamento conceitual que o projeto evita.

### P2 — `as_of` (point-in-time) em toda tool de research
A peça que torna o anti-estado **viável** em vez de só purista. Se cada tool aceita `as_of=<data>` e devolve o snapshot daquela data, a comparação temporal ("o mundo na entrada vs. agora") vira **composição de duas leituras stateless** — a IA chama `fundamentals(AAPL, as_of=entrada)` e `fundamentals(AAPL, as_of=hoje)` e faz o diff, sem o Scout guardar nada. Isso **dissolve metade do grupo de "memória"**: o que parecia exigir estado exige só leitura point-in-time + a data (que a skill guarda). *(Nota: o suporte real a histórico depende da fonte — isso é "o como", fica pra depois; o desenho da assinatura já nasce com `as_of` opcional.)*

### P3 — A tool CALCULA, não CONCLUI — dado + régua explícita, nunca veredito embutido
Uma tool pode fazer aritmética sobre dados (um DCF é aritmética sobre premissas = dado); não pode emitir conclusão ("compre", "risco alto", "tese inválida"). Quando há limiar ("gap relevante", "-6% é anômalo"), **o caller passa o limiar** ou o Scout devolve o valor cru + a régua usada, separados. `thesis_breakers` devolve "guidance cortado 8%, beta 1.4 + a régua", não "VENDA". Assim tudo permanece *sentido*, não *julgamento*.

### P4 — Camada de EVIDÊNCIA com proveniência, não curadoria opinativa
Especialmente no cluster temático: as tools não decretam "X é infra de IA" nem "quem se beneficia de juro baixo". Entregam **associações verificáveis + sensibilidades estatísticas** com a evidência anexa (trecho de filing, % de receita por segmento, pertencimento a ETF temático, beta histórico setor↔driver). A IA conclui. Se o output não pode ser auditado contra uma fonte, é opinião e não é Scout.

### P5 — Lote (batch) é first-class SÓ quando a saída é agregada/filtrada
`watch_signals`, `correlation_matrix`, `news_digest`, `classify` produzem dado **cross-symbol** que um loop de 1-símbolo não reconstrói (correlação só existe em lote). Para "o mesmo dado N vezes" (ex.: `dividends` de um nome), fica por-símbolo e a IA itera. E **scanner market-first ≠ batch-of-symbols**: `movers`/`market_pulse` recebem um *escopo* ("US equities, gap up, volume>X"), não uma lista de símbolos.

### P6 — Meta-tools gordas OK enquanto só AGREGAM dados
`company_dossier` e `risk_readout` são agregadores de leitura legítimos (resolvem o gap de *consistência*: a IA esquece de checar o earnings iminente quando costura 5 tools na mão). Viram problema quando embutem julgamento ou estado, ou quando devolvem sizing/recomendação. Linha vermelha: **descrever risco sim, recomendar ação não.**

### P7 — Nomenclatura sem vocabulário de execução
Nomes que pressupõem trade/conta sugerem acoplamento ao Valet. Renomeações decididas: `pre_trade_brief` → **`risk_readout`** (ou `situation_brief`); `position_diff` → **`changes_since`**. Detecção por chamada usa sufixo **`_check`** (stateless), nunca `_watch` (que implica subscription/relógio).

---

## Superfície de tools consolidada

Legenda: **[v1]** núcleo do MVP · **[v2]** segunda onda · **[skill]** sai do Scout, mora na skill/memória · **[reformular]** mantida só se obedecer aos princípios acima.

### A. Pesquisa por símbolo (núcleo)
| Tool | Status | Notas |
|---|---|---|
| `company_dossier(symbol, depth, as_of)` | v1 | Carro-chefe: agrega em paralelo e consolida. |
| `company_snapshot(symbol)` | v1 | Preço, variação, múltiplos-chave. |
| `fundamentals(symbol, period, as_of)` | v1 | DRE/balanço/fluxo, índices, crescimento. |
| `price_history(symbol, range, interval)` | v1 | OHLCV, com granularidade intraday. |
| `technicals(symbol, timeframe)` | v1 | Expor explicitamente ATR e níveis num. de S/R. |
| `dividends(symbol)` | v1 | Histórico, yield, payout, growth-streak, cortes. Gap nº1 do fundamentalista; dado puro. |
| `valuation_history(symbol, range)` | v1 | Faixa histórica dos próprios múltiplos ("caro vs. ele mesmo"). Dado puro. |
| `quality_metrics(symbol, period)` | v1 | ROIC/ROE/margens em série (proxy de moat). Dado puro. |
| `earnings(symbol)` | v1 | Calendário, histórico, surpresas, estimativas. |
| `news_and_sentiment(symbol, as_of)` | v1 | Só correlação factual com timestamp; **não** afirmar causalidade. |
| `filings(symbol, type)` | v1 | SEC EDGAR 10-K/10-Q/8-K + seções. |
| `analyst_view(symbol)` | v2 | Rating/price target — **dado de terceiros reportado** ("o que dizem"), marcado como opinião externa; nunca síntese própria. |
| `volatility_profile(symbol)` | v2 | ATR, vol implícita, expected move, movimento típico no earnings. Must-have do trader. |
| `liquidity_profile(symbol)` | v2 | Spread, ADV, **volume-by-price** (paredes de liquidez = S/R reais). Dado de negociabilidade, não de execução. |
| `segment_breakdown(symbol)` | v2 | Receita/lucro por segmento e geografia. Sustenta "pureza" temática como dado. |
| `ownership_and_insiders(symbol)` | v2 | 13F / Form 4 — insiders e institucionais. Sinal de convicção; dado público. |
| `capital_allocation(symbol)` | v2 | Buybacks (e a que preço), capex, M&A, dívida. Complemento de `dividends`; teste de gestão racional. |
| `valuation_model(symbol, assumptions)` | reformular/v2 | Ex-`valuation_estimate`. **Faixa parametrizada** com inputs/premissas explícitos — NUNCA "preço justo = X, está barato". O número final é da IA. |

### B. Descoberta / market-first (escopo, não símbolo)
| Tool | Status | Notas |
|---|---|---|
| `screen(criteria)` | v1 | Estender p/ aceitar critérios **técnicos** (RSI, breakout, dist. de média, volume rel.), não só fundamentalistas. |
| `peers(symbol)` | v1 | Concorrentes por sinal **factual** (GICS/SIC, competidores citados em 10-K). Ponte p/ `compare`. |
| `compare(symbols[])` | v1 | Lado a lado (já planejada). |
| `macro_context()` | v1 | Juros, CPI, desemprego, curva (já planejada). |
| `market_pulse(scope)` | v2 | Funde `movers`/`premarket_movers`/`market_pulse`: risk-on/off, VIX, breadth, gappers, volume incomum. Scanner, recebe escopo. |
| `sector_view(sector \| timeframe)` | v2 | Funde `sector_overview` + `sector_performance`: valuation/momentum agregado e rotação. |
| `relative_strength(symbols[], benchmark, period)` | v2 | Ranking de força relativa vs. índice/setor. |
| `etf_holdings(symbol_or_theme)` | v2 | Cesta declarada e pesos. Dado limpo; alavanca temas. |
| `commodity_context()` | v2 | Petróleo/cobre/urânio/ouro como driver. |
| `macro_sensitivity(driver)` | reformular | Ex-`macro_to_sectors`. Entrega **beta/correlação histórica** setor↔driver + a régua, NÃO "quem se beneficia". |
| `theme_map(theme)` | reformular/v2 | Motor de **evidência**, não curador: candidatos via sinais verificáveis (texto de filing, ETFs temáticos, classificação) com a evidência de cada inclusão. |
| `evidence_for(symbol, theme_or_claim)` | v2 | Proveniência: por que X liga (ou não) a um tema/afirmação. O antídoto contra "a IA dentro da tool". |

### C. Lote / monitoramento (stateless — a IA passa a lista a cada chamada)
| Tool | Status | Notas |
|---|---|---|
| `watch_signals(symbols[], thresholds?)` | v1 | Varre N símbolos, retorna só o que "acende" (gap, volume, rompimento, 52wk). Caller passa os limiares. |
| `news_digest(symbols[], since)` | v1 | Manchetes materiais agregadas, deduplicadas, ranqueadas. |
| `calendar(symbols[], window)` | v1 | Earnings + ex-dividendo + splits futuros do conjunto (absorve `earnings_calendar`). |
| `correlation_matrix(symbols[], range)` | v2 | Diversificação real; impossível via loop. |
| `classify(symbols[])` | v2 | Setor/indústria/geo/cap em lote, p/ agregar exposição. |
| `changes_since(symbols[], since)` | v2 | Ex-`position_diff` (nome não sugere estado de conta). Delta de research desde um marco. |
| `factor_exposure(symbols[])` | reformular/v2 | Beta/sensibilidades + régua (evidência), não "RISCO ALTO". |
| `thesis_breakers(symbols[], thesis_facets)` | reformular/v2 | Recebe os pilares da tese **como argumento**; responde quais estão sob ataque pelo dado (evidência). O veredito é da IA. Stateless. |

### D. Detecção de evento (stateless `_check`, nunca `_watch`)
| Tool | Status | Notas |
|---|---|---|
| `catalyst_check(symbol, window)` | v2 | "Houve earnings/evento regulatório/lançamento nesta janela e qual o desfecho?" Lê o mundo, não guarda o que você marcou. |

### E. Meta-agregadores de leitura
| Tool | Status | Notas |
|---|---|---|
| `company_dossier(...)` | v1 | (acima) |
| `risk_readout(symbol)` | v2 | Ex-`pre_trade_brief`. Qualidade + timing técnico + eventos binários próximos + macro num pacote de **leitura**. Sem "trade", sem sizing, sem veredito. Resolve consistência da DD. |

### SAI do Scout → vive na skill / camada de memória [skill]
- `thesis_log` / `thesis_get` / `thesis_list` / `thesis_review` — armazenar o "porquê" e o veredito de tese é **estado + julgamento**.
- `watchlist_add` / `watchlist_review` — pipeline de ideias = estado do usuário.
- `catalyst_watch`, `watch_valuation` — qualquer "me avise quando" = scheduler/estado.

> A skill ESCREVE a tese (num store dela) e, a cada sessão, **passa o texto da tese + a data de entrada** para as tools stateless do Scout (`thesis_breakers`, `changes_since`, `catalyst_check`, `*(as_of)*`) avaliarem contra dados frescos. **Memória vive na skill; verificação vive no Scout.**

---

## Mapa de casos de uso → onde o Scout entra
- **"A AAPL tá cara?"** → `valuation_history` + `quality_metrics` + `dividends`.
- **"O que tá se movendo hoje?"** → `market_pulse(scope)` (scanner).
- **"Como tão minhas 12 posições? Algum alerta?"** → `watch_signals(symbols[])` + `news_digest(symbols[], since)` + `calendar(symbols[])`. (Símbolos vêm do Valet, passados pela IA.)
- **"Me acha players de urânio"** → `theme_map` (evidência) + `etf_holdings` + `peers` + `segment_breakdown`.
- **"A tese da minha AMD quebrou?"** → skill recupera a tese → `thesis_breakers(AMD, facets)` + `changes_since(AMD, since)` + `catalyst_check(AMD, window)`; **a IA dá o veredito**.

---

## Decisões abertas para o usuário
1. **Camada de memória (a maior):** confirmar que tese/watchlist/alertas moram na **skill de estratégia** (workstream separado, depois), e não no Scout. Todo o resto do desenho depende disso.
2. **Escopo do v1:** travar o corte v1 (núcleo por-símbolo + dossier + screen/peers/compare/macro + os 3 batch v1). ~12 tools enxutas em vez de ~35.
3. **`as_of` desde o início:** aceitar que as assinaturas já nasçam com `as_of` opcional, mesmo que algumas fontes grátis só suportem "hoje" no começo.
4. **Narrativa/web:** inalterado — `deep-research`/Workflow + fallback de prompt pro claude.ai web; decidir por benchmark depois.

## O que dá pra atacar primeiro (independente das decisões)
Scaffold (pyproject, layout hexagonal, CI) + **fatia vertical**: adapter yfinance → `company_snapshot`, `fundamentals`, `dividends` (todos dado puro, unânimes como v1). Prova o cano ponta a ponta.
