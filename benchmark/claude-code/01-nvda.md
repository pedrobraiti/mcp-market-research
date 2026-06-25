# NVIDIA (NVDA) — Análise de Investimento Aprofundada

**Data-base: 25 de junho de 2026**
**Preço de referência: ~US$ 200,04 (fechamento de 23/06/2026) | Market cap: ~US$ 4,85–4,88 trilhões**

> Nota metodológica: todos os números abaixo estão referenciados na seção **Fontes**. Onde fontes divergem (ex.: EPS GAAP vs. não-GAAP, P/E spot), o relatório sinaliza a divergência explicitamente. Atenção ao calendário fiscal: o ano fiscal da NVIDIA termina em janeiro, então o **FY2026** (encerrado em jan/2026) já é histórico, e a empresa reportou o **Q1 FY2027** (trimestre encerrado em 27/04/2026) em 21/05/2026 — esse é o trimestre mais recente disponível na data-base.

---

## 1. Sumário executivo

A NVIDIA chega a junho de 2026 ainda como a empresa dominante da infraestrutura de IA, com receita recorde e visibilidade de pedidos sem precedentes (Jensen Huang citou **>US$ 1 trilhão em pedidos cumulativos de Blackwell + Vera Rubin até 2027** no GTC 2026). Ao mesmo tempo, a tese mudou de "crescimento inquestionável" para "crescimento abundante, porém cercado de riscos crescentes": concorrência real do **custom silicon dos hyperscalers** (sobretudo o TPU do Google), o avanço da **AMD** com a linha MI400/MI450 ancorada em megacontratos da OpenAI e da Meta, a **saga regulatória da China** (que segue fora do guidance), e um debate público sobre **financiamento circular** e **contabilidade de depreciação** liderado por céticos como Michael Burry.

Paradoxo central da data-base: apesar de fundamentos recordes, a ação **caiu ~15% desde a máxima histórica** de US$ 235,47 (14/05/2026) e acumula alta modesta de **~7% no ano**, com o **forward P/E comprimido para ~20–23x** — patamar historicamente baixo para o papel. O mercado, em outras palavras, já está precificando desaceleração e risco de ciclo.

---

## 2. Fundamentos recentes (a base de tudo)

### 2.1 Resultado mais recente — Q1 FY2027 (encerrado em 27/04/2026, reportado em 21/05/2026)

| Métrica | Valor | Crescimento |
|---|---|---|
| Receita total | **US$ 81,6 bi** | +85% A/A, +20% T/T |
| Data Center (total) | **US$ 75,2 bi** | +92% A/A, +21% T/T |
| — DC Computing | US$ 60,4 bi | +77% A/A, +18% T/T |
| — DC Networking | US$ 14,8 bi | +199% A/A, +35% T/T |
| Margem bruta GAAP | **74,9%** | — |
| Margem bruta não-GAAP | **75,0%** | — |
| EPS diluído **não-GAAP** | **US$ 1,87** | +140% A/A (bateu consenso de US$ 1,77) |
| EPS diluído **GAAP** | **US$ 2,39** | +214% A/A |
| Lucro líquido (GAAP) | **US$ 58,3 bi** | — |
| Free cash flow | **US$ 49 bi** | (vs. US$ 35 bi no tri anterior) |

> **Cuidado com o EPS:** algumas manchetes (ex.: Yahoo Finance) reportaram "EPS GAAP de US$ 1,87". Cruzando com o detalhamento da StockTitan/8-K, o **US$ 1,87 é o número não-GAAP**; o GAAP foi **US$ 2,39**. O GAAP foi inflado por **ganhos com participações acionárias** (a carteira de equity da NVIDIA — OpenAI, CoreWeave, etc.), o que ajuda a explicar lucro líquido GAAP de US$ 58,3 bi. Isso é relevante para o bear case de "qualidade dos lucros".

**Retornos de capital:** dividendo trimestral elevado de US$ 0,01 para **US$ 0,25 por ação (aumento de 25x)**; nova autorização de recompra de **US$ 80 bi** (sem expiração); US$ 20 bi devolvidos no trimestre.

### 2.2 Guidance Q2 FY2027

- Receita: **US$ 91,0 bi (±2%)** — implicaria ~+11% T/T.
- Margem bruta GAAP/não-GAAP: **74,9% / 75,0% (±50 pb)**.
- **Crucial: o guidance NÃO assume nenhuma receita de Data Center compute vinda da China**, refletindo a incerteza de licenciamento do H200. Ou seja, qualquer volume chinês aprovado seria *upside* sobre os US$ 91 bi.

### 2.3 Contexto anual — FY2026 (encerrado jan/2026)

- Receita total: **US$ 215,9 bi**, +65% A/A.
- Data Center FY2026: **US$ 193,7 bi**, +68% A/A.
- Lucro líquido FY2026: **~US$ 117,0 bi**, +58% A/A.
- Sovereign AI: mais que triplicou para **>US$ 30 bi** no FY2026 (Reino Unido, França, Holanda, Canadá, Singapura como principais).
- ~9 gigawatts de capacidade Blackwell implantados por hyperscalers/clouds/enterprises ao longo do ano.

---

## 3. Posição competitiva e ameaças

A NVIDIA ainda detém **~80% do mercado de aceleradores de IA em 2026** (estimativas variam ~75–92% conforme a metodologia e se incluem ASICs internos). O fosso continua sendo **CUDA + NVLink + a cadência anual de produto + a oferta de "AI factory" full-stack (compute + networking + software)**. Mas a estrutura da ameaça mudou de "inexistente" para "tripla e simultânea".

### 3.1 Custom silicon dos hyperscalers — a ameaça mais estrutural

Este é, na visão de boa parte dos analistas, um risco **maior e de crescimento mais rápido** que a AMD, porque ataca diretamente os maiores clientes da NVIDIA (que também são os fornecedores das próprias alternativas).

- **Google TPU v7 "Ironwood"** (GA em 2026) é o desafiante mais credível. Especs citadas: ~4,6 PFLOPS FP8 por chip (ligeiramente acima do B200, ~4,5 PFLOPS), pod de 9.216 chips em topologia de toro 3D. SemiAnalysis tratou o TPU como "o gorila de 400 kg na sala".
- **O contrato Anthropic–Google** é o sinal de alarme: até **1 milhão de TPUs** (~400k Ironwoods em racks vendidos via Broadcom, ~US$ 10 bi; +600k via aluguel no GCP, ~US$ 42 bi de RPO). Há relatos de negociações com **Meta** para usar TPUs (aluguel a partir de 2026, hardware próprio a partir de 2027) — seria a primeira "deserção" de um hyperscaler na infraestrutura de *treino*.
- TCO citado: TPU pode custar ~30% menos por hora que GB200 e ~41% menos que GB300 em certas cargas.
- **Sinal de fraqueza admitido:** Huang reconheceu publicamente que *não* ter investido cedo na Anthropic foi um erro estratégico — admissão de vulnerabilidade incomum vinda da NVIDIA.
- Demais ASICs: **AWS Trainium**, **Microsoft Maia**, **Meta MTIA** — todos desenhados para reduzir dependência da GPU merchant. A tese de inferência ("inferência já é 80–90% da carga de compute") favorece ASICs especializados em produção.

### 3.2 AMD — concorrência real, mas ainda distante em escala

- Market share da AMD em aceleradores estimado em **~5–7%** (Instinct gerou ~US$ 7–8 bi em 2025).
- **MI400/MI450 (2026):** plataforma Helios (rack com 72 MI455X, 31 TB HBM4, ~2,9 ExaFLOPS FP4); MI400 com até 432 GB HBM4. Migração para **TSMC 2nm** (primeiras GPUs em 2nm).
- **Megacontratos dão visibilidade à AMD:** OpenAI (6 GW a partir do 2S26, "double-digit billions" de receita/ano por GW, segundo Lisa Su) e **Meta** (6 GW, MI450 + Epyc "Venice", warrant de 160M ações). Volume inicial do Helios no 3T26, ramp forte no 4T26/1T27.
- Financeiro AMD Q1 2026: receita US$ 10,25 bi (+38% A/A), DC US$ 5,8 bi; guidance Q2 ~US$ 11,2 bi. Ainda **uma fração** dos US$ 75 bi/tri de DC da NVIDIA.
- Leitura: a AMD valida que há um "segundo fornecedor" viável (importante para o poder de barganha dos clientes e para teto de preços/margem da NVIDIA), mas não ameaça a liderança de volume no horizonte de 12 meses.

### 3.3 China — o risco regulatório que não sai do lugar

- **Histórico:** as restrições de abril/2025 ao **H20** custaram à NVIDIA **US$ 4,5 bi de baixa** (estoque/obrigações de compra) e ~US$ 2,5 bi de receita não embarcada no trimestre, com ~US$ 8 bi de impacto guidado para o Q2 FY2026. A NVIDIA estima o mercado chinês de aceleradores de IA em ~US$ 50 bi.
- **Estado em jun/2026:** os EUA **liberaram o H200** para a China sob condições — inspeção nos EUA, **tarifa/"duty" de 25%**, **teto de 75.000 unidades por cliente** e ~10 empresas aprovadas (Alibaba, Tencent, ByteDance, etc.). Há preparativos para enviar dezenas de milhares de GPUs.
- **O problema agora é Pequim, não Washington:** empresas chinesas recuaram após orientação do governo chinês para priorizar alternativas domésticas (Huawei Ascend, etc.). Não há aprovação formal de Pequim para as importações.
- **Implicação para a tese:** como a China está **zerada no guidance**, o downside já está, em tese, precificado — e qualquer destravamento é **opção comprada de graça** (upside). O risco real é que a China se torne permanentemente um mercado perdido para chips de ponta da NVIDIA, consolidando concorrentes domésticos.

---

## 4. Principais riscos para os próximos 12 meses

1. **Digestão de CapEx / ciclo dos hyperscalers.** Dois clientes representaram **39% da receita** no Q2 FY2026 (um cliente sozinho = 23%). Essa concentração é faca de dois gumes: qualquer pausa de CapEx de 1–2 megaclientes move o número. O bull narrative depende de hyperscaler CapEx "se aproximando de US$ 1 trilhão".

2. **Financiamento circular / fragilidade da demanda.** A NVIDIA comprometeu **>US$ 40 bi em deals de equity em 2026**, com destaque para **até US$ 100 bi na OpenAI** (parceria de 10 GW, anunciada em set/2025). O loop "NVIDIA investe na OpenAI → OpenAI contrata clouds (Oracle, CoreWeave) → clouds compram GPUs da NVIDIA" gera receita parcialmente autofinanciada. A OpenAI deve **perder ~US$ 14 bi em 2026**. Bloomberg estima **>US$ 800 bi** em arranjos circulares no ecossistema. Paralelo recorrente com o *vendor financing* da bolha d2026 ponto-com.

3. **Qualidade dos lucros (Burry).** Michael Burry argumenta que hyperscalers **subdepreciam** GPUs (5–6 anos contábeis vs. vida econômica real de 2–3 anos), inflando lucros do setor em **~US$ 176 bi entre 2026–2028**, e que a NVIDIA destrói "owner's earnings" via SBC pesado. A NVIDIA enviou memorando a analistas sell-side rebatendo. É um risco de *narrativa/múltiplo* mais que de fluxo de caixa imediato.

4. **Erosão de market share e de preço.** Combinação TPU + MI450 + ASICs pode, na margem, reduzir o share da NVIDIA (de ~80% rumo a ~75% em algumas projeções) e pressionar precificação — exatamente quando a margem bruta já está no teto histórico (~75%), deixando pouco espaço para expansão e algum risco de compressão.

5. **Gargalos físicos (energia, HBM, packaging).** O ramp do Rubin depende de HBM4 (SK Hynix, Micron) e CoWoS (TSMC); há a "HBM crunch". Energia elétrica para data centers é restrição real ao ritmo de implantação.

6. **Execução do Rubin.** Transição arquitetural (Blackwell → Vera Rubin no 2S26). Atrasos de ramp/yield, como ocorreu no início do Blackwell, afetariam o 2S26.

7. **Valuation/sentimento.** Com a ação já corrigindo ~15% do topo, o papel está sensível a qualquer decepção em guidance ou a um "air pocket" de demanda — múltiplo comprimido não impede quedas se as estimativas de EPS forem cortadas.

---

## 5. Valuation — frente ao próprio histórico e aos pares

### 5.1 Frente ao próprio histórico

| Janela | P/E (trailing, aprox.) |
|---|---|
| Pico abr/2023 (trailing) | ~138x (extremo pós-pandemia/baixo lucro) |
| 2023 (fim) | ~80,7x |
| 2024 (fim) | ~80,5x |
| 2025 (fim) | ~45,9x |
| Mínima 5 anos (jan/2026) | ~40,8x |
| Média histórica 10 anos | ~53,7x |
| **Atual (meados jun/2026)** | **~30–35x trailing** |

- **Forward P/E:** fontes divergem entre **~20x e ~23,4x** (gurufocus ~22,6x em 23/06; valueinvesting.io ~20x). Em qualquer leitura, é o **patamar mais baixo da era IA** para o papel.
- A compressão é dramática: o trailing P/E de ~30x está **~33% abaixo da média de 12 meses (~46x)**. O mercado está pagando *menos* por dólar de lucro mesmo com o lucro crescendo ~85% A/A — sinal clássico de "pico de ciclo precificado" / ceticismo sobre durabilidade.

### 5.2 Frente aos pares

- Forward P/E da NVIDIA (~22,6x) está **~42% abaixo da mediana de semis (~38,8x)**.
- Em P/E "value-screen", NVIDIA (~31,7x) aparece barata vs. média de pares de ~102x (essa média é distorcida por nomes de lucro baixo). Mais baixa que AMD; mais alta que MSFT e QCOM em certos cortes.
- **PEG:** com EPS crescendo dezenas de % e forward P/E ~20x, o PEG implícito é **<1**, o que sustenta o argumento "GARP" (growth at a reasonable price) do bull case — desde que se acredite nas estimativas.

### 5.3 Estimativas e price targets

- **EPS FY2027 consenso:** revisado para cima, ~**US$ 9,3** (Simply Wall St); Morgan Stanley usa **US$ 13,08** para 2027 (provável base calendário/ano-cheio adiante).
- **Morgan Stanley:** Overweight, **alvo US$ 288** (22x sobre EPS 2027 de US$ 13,08); em outra nota, alvo US$ 285 sobre tese de DC de US$ 1 tri, projetando **US$ 884 bi de receita de DC em CY2026–27** vs. consenso de ~US$ 785 bi. Mantém NVDA como Top Pick do grupo de processadores e "best value in the sector".

---

## 6. Bull case (articulado)

1. **Visibilidade de pedidos sem precedente.** >US$ 500 bi de backlog Blackwell+Rubin já reconhecido, e Huang sinalizou **>US$ 1 tri cumulativo até 2027** no GTC 2026. Se a oferta acompanhar, é um ciclo multi-anual, não um pico.
2. **Margem e fluxo de caixa excepcionais.** Margem bruta ~75%, FCF de US$ 49 bi/tri, US$ 80 bi de recompra autorizada, dividendo 25x maior — máquina de caixa que dá colchão e flexibilidade.
3. **Transição treino → inferência favorece a NVIDIA full-stack.** Inferência já é 80–90% da carga; CUDA + NVLink + networking (Spectrum-X/InfiniBand, +199% A/A) entregam TCO de sistema, não só FLOPS de chip.
4. **Diversificação além do hyperscaler.** "Segunda categoria" de Huang — clouds regionais, enterprise, **sovereign AI (>US$ 30 bi e triplicando)** — cresce mais rápido e é onde o custom silicon não chega.
5. **Cadência anual imbatível.** Blackwell (2024) → Blackwell Ultra (2025) → **Vera Rubin (2S26, ~3,3x throughput vs. B300, ~50 PFLOPS FP4, 288 GB HBM4)** → Rubin Ultra (2027) → Feynman (2028). Mantém o gap de performance/eficiência sobre AMD e ASICs.
6. **Valuation barato vs. histórico e crescimento.** Forward P/E ~20–23x com lucro crescendo ~85% A/A; PEG <1. Se a tese de demanda se concretizar, o múltiplo é defensável e há espaço de reprecificação.
7. **China é opcionalidade gratuita.** Como está zerada no guidance, qualquer destravamento de H200 (com taxa de 25%) é upside puro.

## 7. Bear case (articulado)

1. **Demanda autofinanciada e circular.** >US$ 40 bi/ano em equity deals, US$ 100 bi na OpenAI (que perde US$ 14 bi/ano), >US$ 800 bi de arranjos circulares no ecossistema. Se o ROI da IA decepcionar, a queda de CapEx atinge simultaneamente a receita *e* a carteira de investimentos da NVIDIA — efeito cascata estilo *vendor financing* dot-com.
2. **Concentração de clientes.** 39% da receita em 2 clientes; 61% em 4. Esses mesmos clientes constroem alternativas (TPU, Trainium, Maia, MTIA, MI450). Conflito de interesse estrutural.
3. **Custom silicon é real e está vencendo deals de marca.** Anthropic (1M TPUs), Meta avaliando TPU, OpenAI/Meta na AMD. O "monopólio" já tem rachaduras públicas — e o próprio Huang admitiu vulnerabilidade.
4. **Qualidade dos lucros sob ataque.** Tese de Burry sobre subdepreciação (US$ 176 bi 2026–28) e SBC; ganhos de equity inflando o lucro GAAP (US$ 58,3 bi com a ajuda de mark-to-market de participações). Risco de "des-rate" do múltiplo se a narrativa pegar.
5. **Margem no teto = só tem para onde cair.** 75% de margem bruta com AMD oferecendo TCO menor e ASICs internos a custo marginal pressiona preço/mix justamente quando não há mais alavanca de expansão de margem.
6. **China pode ser perda permanente.** Pequim empurrando para fornecedores domésticos pode tornar um mercado de ~US$ 50 bi estruturalmente fechado, fortalecendo concorrentes (Huawei) que depois exportam.
7. **Risco de ciclo já visível na ação.** -15% do topo, +7% no ano apesar de lucros recordes: o mercado pode estar antecipando que FY2027/28 marca o pico de crescimento de margem incremental e de share.

---

## 8. Síntese / leitura de investimento

- **O debate não é mais "a NVIDIA é boa empresa?" — é "quanto do ciclo é estrutural vs. pico?".** Os fundamentos são extraordinários e a visibilidade de backlog é genuína; o múltiplo está barato vs. história. Esse é o esqueleto do bull case GARP.
- **O que mudou materialmente vs. 12–18 meses atrás:** (i) custom silicon deixou de ser teórico (Anthropic/Google, Meta avaliando); (ii) AMD ganhou contratos-âncora (OpenAI, Meta); (iii) surgiu um debate sério sobre **qualidade contábil** e **financiamento circular**; (iv) a ação parou de subir mesmo com lucros recordes.
- **Gatilhos a monitorar nos próximos 12 meses:** ramp do Vera Rubin no 2S26 (yield/HBM4/CoWoS); confirmação de destravamento da China (Pequim); sinais de digestão de CapEx dos top-2 clientes; eventuais "deserções" adicionais para TPU/MI450; e como o lucro GAAP se comporta sem ajuda de ganhos de equity.
- **Assimetria:** com China zerada no guidance e múltiplo comprimido, há colchão; mas concentração de clientes + financiamento circular + margem no teto formam um conjunto de riscos *correlacionados* que podem disparar juntos num eventual "AI air pocket".

---

## Fontes

**Resultados e guidance (Q1 FY2027 / FY2026):**
- StockTitan — "NVIDIA Q1 revenue hits $81.6B, ups dividend, buyback" — https://www.stocktitan.net/news/NVDA/nvidia-announces-financial-results-for-first-quarter-fiscal-fq78amc9h84m.html
- Futurum Group — "NVIDIA Q1 FY2027: Data Center Diversification, Blackwell Scale, CPU Upside" — https://futurumgroup.com/insights/nvidia-q1-fy2027-data-center-diversification-blackwell-scale-cpu-upside/
- Yahoo Finance — "Nvidia Q1 FY2027 earnings: record revenue, dividend hike" — https://finance.yahoo.com/markets/stocks/articles/nvidia-q1-fy2027-earnings-record-214649637.html
- moltbook — "Nvidia Q1 FY2027 data center revenue $39.1B / +73% YoY" — https://moltbook.com/post/1f343e12-88da-4ee3-a0a1-bf4a49e0221e
- IndMoney — "Nvidia Reports $81.6B Revenue, Raises Dividend 25x" — https://www.indmoney.com/blog/us-stocks/nvidia-stock-q1-fy27-earnings-81b-revenue-25x-dividend
- NVIDIA 8-K / Form 8-K FY2026 (Q1 FY2027 press release, EDGAR) — https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000051/q1fy27pr.htm
- NVIDIA CFO Commentary Q1 FY2027 (EDGAR) — https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000051/q1fy27cfocommentary.htm
- Yahoo Finance — "Nvidia posts record $215 billion annual revenue… gaming GPUs now only 11.45%" — https://finance.yahoo.com/news/nvidia-posts-record-215-billion-102845670.html
- TheEnergyMag — "NVIDIA Reports $215.9 Billion in FY2026 Revenue as Data Center Networking Surges 142%" — https://theenergymag.com/news/market-news/nvidia-reports-215-9-billion-in-fy-2026-revenue-as-data-center-networking-surges-142
- Futurum — "NVIDIA Q4 FY2026 Earnings: Durable AI Infrastructure Demand" — https://futurumgroup.com/insights/nvidia-q4-fy-2026-earnings-highlight-durable-ai-infrastructure-demand/

**Valuation:**
- GuruFocus — "NVIDIA Forward PE Ratio: 22.57" — https://www.gurufocus.com/term/forward-pe-ratio/NVDA
- valueinvesting.io — "NVIDIA Forward P/E" — https://valueinvesting.io/NVDA/metric/forward-pe
- Macrotrends — "NVIDIA PE Ratio 2012-2026" — https://www.macrotrends.net/stocks/charts/NVDA/nvidia/pe-ratio
- fullratio — "NVDA Nvidia PE ratio current and historical" — https://fullratio.com/stocks/nasdaq-nvda/pe-ratio
- public.com — "NVIDIA (NVDA) P/E Ratio: Current & Historical" — https://public.com/stocks/nvda/pe-ratio
- Simply Wall St — "NVIDIA Valuation, Peer Comparison & Price Targets" — https://simplywall.st/stocks/us/semiconductors/nasdaq-nvda/nvidia/valuation
- Simply Wall St — "NVIDIA Stock Forecast & Analyst Predictions" (EPS FY2027) — https://simplywall.st/stocks/us/semiconductors/nasdaq-nvda/nvidia/future
- TheStreet — "Morgan Stanley Unveils Bold New Price Target on Nvidia" — https://www.thestreet.com/investing/stocks/morgan-stanley-sets-bold-new-price-target-on-nvidia-stock
- Investing.com — "Morgan Stanley reiterates Overweight on Nvidia, $288 target" — https://www.investing.com/news/analyst-ratings/morgan-stanley-reiterates-overweight-on-nvidia-stock-288-target-93CH-4723640
- Investing.com — "Morgan Stanley reiterates Overweight, $260 target" — https://www.investing.com/news/analyst-ratings/morgan-stanley-reiterates-overweight-on-nvidia-stock-260-target-93CH-4565172
- MarketBeat — "NVDA Stock Forecast and Price Target 2026" — https://www.marketbeat.com/stocks/NASDAQ/NVDA/forecast/

**Preço / desempenho da ação:**
- Macrotrends — "NVIDIA 15 Year Stock Price History" — https://www.macrotrends.net/stocks/charts/NVDA/nvidia/stock-price-history
- Capital.com — "NVIDIA Market Cap (NVDA) – June 2026 Update" — https://capital.com/en-int/markets/shares/nvidia-corp-share-price/market-cap
- financecharts — "NVIDIA Total Return YTD/TTM" — https://www.financecharts.com/stocks/NVDA/performance/total-return

**Concorrência — AMD:**
- DataCenterDynamics — "AMD posts Q1 2026 data center revenue of $5.8bn" — https://www.datacenterdynamics.com/en/news/amd-posts-q1-2026-data-center-revenue-of-58bn-forecasts-120bn-server-cpu-income-by-2030/
- Ticker Report — "AMD Expands Meta AI Deal: 6GW Instinct GPU, MI450, 160M-Share Warrant" — https://www.tickerreport.com/banking-finance/13358082/advanced-micro-devices-expands-meta-ai-deal-6gw-instinct-gpu-plan-custom-mi450-and-160m-share-warrant.html
- adwaitx — "OpenAI and AMD: 6GW MI450 Deal Starts 2026" — https://www.adwaitx.com/openai-amd-partnership-mi450-6gw-2026/
- wccftech — "AMD Instinct MI455X & MI430X Accelerators in 2026" — https://wccftech.com/amd-to-battle-nvidia-ai-dominance-instinct-mi400-accelerators-2026-mi500-2027/
- Silicon Analysts — "AMD vs NVIDIA AI GPU Market Share 2026" — https://siliconanalysts.com/analysis/amd-vs-nvidia-ai-gpu-market-share-2026

**Concorrência — custom silicon / hyperscalers:**
- SemiAnalysis — "Google TPUv7: The 900lb Gorilla In the Room" — https://newsletter.semianalysis.com/p/tpuv7-google-takes-a-swing-at-the
- BW Businessworld — "Google TPUs, Gemini 3, Claude 4.5 Break Nvidia, OpenAI Monopoly" — https://www.businessworld.in/article/google-tpu-anthropic-claude-break-nvidia-monopoly-581947
- tech-insider — "Google $40B Anthropic Investment: TPU Deal Inside" — https://tech-insider.org/google-40-billion-anthropic-investment-tpu-compute-2026/
- io-fund — "Google TPU v8 vs Nvidia: How Inference Is Rewriting the AI Market" — https://io-fund.com/ai-stocks/google-tpu-v8-vs-nvidia-inference-rewrites-ai-market
- Silicon Analysts — "NVIDIA AI Accelerator Market Share 2024–2026" — https://siliconanalysts.com/analysis/nvidia-ai-accelerator-market-share-2024-2026

**China / restrições de exportação:**
- Bloomberg — "Nvidia Gets US License for Small Amount of H200 Exports to China" — https://www.bloomberg.com/news/articles/2026-02-26/nvidia-gets-us-license-for-small-amount-of-h200-exports-to-china
- CNBC — "U.S. clears H200 chip sales to 10 China firms" — https://www.cnbc.com/2026/05/14/us-clears-h200-chip-sales-to-10-china-firms-as-nvidia-ceo-looks-for-breakthrough.html
- Tom's Hardware — "Nvidia prepares shipment of 82,000 AI GPUs to China… 25% tax" — https://www.tomshardware.com/tech-industry/semiconductors/nvidia-prepares-h200-shipments-to-china-as-chip-war-lines-blur
- Tom's Hardware — "Nvidia says H200 demand in China is 'very high'" — https://www.tomshardware.com/pc-components/gpus/nvidia-says-h200-demand-in-china-is-very-high-as-export-licenses-near-completion
- Computer Weekly — "Nvidia takes $4.5bn hit due to export restrictions" — https://www.computerweekly.com/news/366625005/Nvidia-takes-45bn-hit-due-export-restrictions
- Futurum — "NVIDIA Q1 FY2026 Revenue Jumps 69% Despite China Export Setback" — https://futurumgroup.com/insights/nvidia-q1-fy-2026-revenue-jumps-69-despite-china-export-setback/

**Roadmap Rubin / GTC 2026 / backlog:**
- CNBC — "Nvidia GTC 2026: Jensen Huang sees $1 trillion in orders for Blackwell and Vera Rubin through '27" — https://www.cnbc.com/2026/03/16/nvidia-gtc-2026-ceo-jensen-huang-keynote-blackwell-vera-rubin.html
- TechCrunch — "Jensen put Nvidia's Blackwell and Vera Rubin projections into the $1 trillion stratosphere" — https://techcrunch.com/2026/03/16/jensen-just-put-nvidias-blackwell-and-vera-rubin-sales-projections-into-the-1-trillion-stratosphere/
- Tom's Hardware — "Nvidia announces Rubin GPUs in 2026, Rubin Ultra in 2027, Feynman added to roadmap" — https://www.tomshardware.com/pc-components/gpus/nvidia-announces-rubin-gpus-in-2026-rubin-ultra-in-2027-feynam-after
- DataCenterKnowledge — "GTC 2026: Nvidia Unveils Vera Rubin AI Platform, Eyes $1T by 2027" — https://www.datacenterknowledge.com/data-center-chips/gtc-2026-nvidia-unveils-vera-rubin-ai-platform-eyes-1t-by-2027
- NVIDIA Newsroom — "NVIDIA Vera Rubin Ramps Into Full Production" — https://nvidianews.nvidia.com/news/vera-rubin-full-production-agentic-ai-factory

**Riscos — financiamento circular / bolha / contabilidade:**
- Bloomberg — "AI Circular Deals: How Microsoft, OpenAI and Nvidia Keep Paying Each Other" — https://www.bloomberg.com/graphics/2026-ai-circular-deals/
- Crypto Briefing — "Nvidia commits over $40B to AI equity deals in 2026, raising dot-com era comparisons" — https://cryptobriefing.com/nvidia-40b-ai-equity-deals-2026/
- io-fund — "Nvidia, CoreWeave, and Nebius: Inside the Circular Financing of the GPU Boom" — https://io-fund.com/ai-stocks/nvidia-coreweave-nebius-circular-financing-gpu-boom
- CNBC — "Michael Burry accuses AI hyperscalers of artificially boosting earnings" — https://www.cnbc.com/2025/11/11/big-short-investor-michael-burry-accuses-ai-hyperscalers-of-artificially-boosting-earnings.html
- TheStreet — "Michael Burry doubles down on stock market, AI message for 2026" — https://www.thestreet.com/investing/stocks/michael-burry-doubles-down-on-stock-market-ai-message-for-2026
- Stocktwits — "Michael Burry Vs. Nvidia Heats Up… NVIDIA privately denies 'Enron-like fraud'" — https://stocktwits.com/news-articles/markets/equity/michael-burry-vs-nvidia-heats-up-big-short-investor-stands-by-his-analysis/cL524BTREX7

**Concentração de clientes / OpenAI:**
- TechCrunch — "Nvidia says two mystery customers accounted for 39% of Q2 revenue" — https://techcrunch.com/2025/08/30/nvidia-says-two-mystery-customers-accounted-for-39-of-q2-revenue/
- DataCenterDynamics — "Two unnamed customers accounted for almost 40% of Nvidia's Q2 2026 revenue" — https://www.datacenterdynamics.com/en/news/two-unnamed-customers-accounted-for-almost-40-of-nvidias-q2-2026-revenue/
- CNBC — "Nvidia plans to invest up to $100 billion in OpenAI" — https://www.cnbc.com/2025/09/22/nvidia-openai-data-center.html
- NVIDIA Newsroom — "OpenAI and NVIDIA Announce Strategic Partnership to Deploy 10 Gigawatts" — https://nvidianews.nvidia.com/news/openai-and-nvidia-announce-strategic-partnership-to-deploy-10gw-of-nvidia-systems
- NVIDIA 10-Q FY2026 (EDGAR) — https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000052/nvda-20260426.htm

---

*Disclaimer: relatório informacional de pesquisa, não constitui recomendação de investimento. Valores de mercado e múltiplos flutuam diariamente; confirme os números na data da decisão.*
