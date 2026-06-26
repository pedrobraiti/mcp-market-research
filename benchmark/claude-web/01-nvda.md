# NVIDIA (NVDA): Análise de Investimento Aprofundada — Data-Base Junho de 2026

> **Aviso legal (disclaimer):** Este relatório tem caráter exclusivamente informativo e educacional. **Não constitui recomendação de compra, venda ou manutenção** de qualquer valor mobiliário, nem aconselhamento financeiro, contábil, jurídico ou tributário. Projeções, preços-alvo e cenários são estimativas sujeitas a erro e a mudanças sem aviso. Faça sua própria diligência (*due diligence*) ou consulte um profissional habilitado antes de investir. O autor pode não deter posição na ação. Investimentos envolvem risco de perda de capital.

---

## TL;DR

- **A NVIDIA continua dominante e em forte aceleração, e a ação não está cara para o crescimento.** No 1º trimestre do ano fiscal de 2027 (reportado em 20/05/2026), a empresa registrou receita recorde de **US$ 81,6 bilhões (+85% a/a)**, com Data Center de **US$ 75,2 bilhões (+92% a/a)**, EPS non-GAAP de US$ 1,87 (+140% a/a) e *free cash flow* recorde de **US$ 48,6 bilhões**. Com backlog Blackwell+Rubin de **~US$ 500 bilhões** até o fim de 2026, a ação (negociando em torno de US$ 205–220, *market cap* ~US$ 5 trilhões) tem **P/L forward de ~20–23x** — surpreendentemente modesto. O debate deixou de ser "a demanda é real?" e passou a ser "quanto já está no preço e por quanto tempo dura".
- **As ameaças são reais, porém — no horizonte de 12 meses — secundárias.** *Custom silicon* dos hyperscalers (Google TPU, AWS Trainium) e a AMD (MI400/deal OpenAI) erodem a participação no mercado *amplo* de aceleradores de IA (de ~86% em 2024 para projetados ~75% em 2026); a China foi praticamente zerada para vendas novas de chips avançados; e a concentração de clientes é extrema (2 clientes = 39% da receita). Mesmo assim, o fosso competitivo (*moat*) de CUDA + networking + cadência anual de produtos permanece intacto.
- **Cenários de preço (12 meses):** **bear ~US$ 130–150** (desaceleração de capex + compressão de múltiplo), **base ~US$ 270–300** (consenso; P/L ~30x sobre EPS FY27 de ~US$ 8), **bull ~US$ 360–490** (manutenção de múltiplo + execução da Rubin + retorno parcial da China). O perfil risco/retorno favorece capital paciente, mas com volatilidade alta (beta ~2,2).

---

## Key Findings (Principais Constatações)

1. **Resultados recordes e aceleração de receita.** Receita do ano fiscal de 2026 (encerrado em 25/01/2026) de **US$ 215,9 bilhões (+65%)**; Data Center de **US$ 193,7 bilhões (+68%)**, ~90% da receita total. No 1T FY2027: **US$ 81,6 bi (+85% a/a, +20% t/t)**, terceiro trimestre consecutivo de aceleração; EPS non-GAAP de US$ 1,87; lucro líquido GAAP de US$ 58,3 bilhões; FCF de US$ 48,6 bilhões. *Guidance* do 2T FY27: **"Revenue is expected to be $91.0 billion, plus or minus 2%. We are not assuming any Data Center compute revenue from China in our outlook"**, com margem bruta non-GAAP de 75,0% ±50 bps.
2. **Margem bruta recuperada.** Caiu a 61,0% (non-GAAP) no 1T FY26 por conta do *charge* de US$ 4,5 bilhões do H20; recuperou para **75,2% no 4T FY26 e 75,2% no 1T FY27**. Margem bruta cheia do FY26: 71,3% non-GAAP.
3. **Roadmap intacto e acelerado.** Blackwell/Blackwell Ultra (GB300) em pleno *ramp* (B300 já é ~2/3 das vendas Blackwell); **Vera Rubin em produção plena**, primeiros embarques no 3T 2026 e *ramp* de volume no 4T; Rubin Ultra em 2027 e Feynman em 2028 — **cadência anual** declarada por Jensen Huang.
4. **Concorrência crescente, mas atrás.** AMD MI355X (288GB HBM3e, 8TB/s) competitiva em inferência; MI400/MI450 "Helios" no 2S2026 (432GB HBM4); *deal* OpenAI de 6GW. Participação da AMD em aceleradores de IA ~5–7%. *Custom silicon*: Broadcom guia **~US$ 56 bilhões de receita de semicondutores de IA em FY2026**; Google TPU v7 "Ironwood"; AWS Trainium3.
5. **China praticamente zerada.** Participação de vendas novas de chips avançados caiu de ~95% para ~zero; *charge* de US$ 4,5 bilhões e ~US$ 8 bilhões de receita perdida no 2T FY26. H200 aprovado condicionalmente (taxa de 25% ao governo dos EUA) mas **sem receita realizada**.
6. **Valuation:** P/L *trailing* ~30–35x, forward ~20–23x, EV/EBITDA ~29x (vs. média de 5 anos ~57x), EV/Sales ~22x, PEG ~0,44. Preço-alvo médio dos analistas ~US$ 270–310 (faixa US$ 130–500), rating consensual **"Strong Buy"**.

---

## Details (Análise Detalhada)

### (a) Posição Competitiva Atual e Ameaças

**Participação de mercado.** A NVIDIA controla cerca de **94% do mercado de GPUs discretas** (Jon Peddie Research, 4T2025 — ganho de ~10 p.p. a/a; AMD caiu a 5% e Intel estável em 1%, de 11,48 milhões de placas AIB embarcadas) e mais de 90% dos *workloads* de IA em nuvem. No mercado *amplo* de aceleradores de IA por receita, estimativas de Mercury Research/SemiAnalysis (compiladas por analistas) apontam ~86% em 2024, com **projeção de queda para ~75% em 2026** conforme os ASICs escalam. A AMD detém ~5–7%. **Atenção:** as cifras de share do mercado amplo de aceleradores são estimativas/projeções, não dados auditados — a queda para ~75% é projetada, não realizada.

**Roadmap de produtos.** Blackwell foi o *ramp* mais rápido da história da empresa; B300/GB300 já representam dois terços das vendas Blackwell. A **Vera Rubin** foi anunciada em produção plena no Computex/GTC Taipei (31/05–01/06/2026), unificando racks NVL72, CPU Vera, BlueField-4 e Spectrum-X Ethernet Photonics, com 10x throughput de agentes vs. Grace Blackwell. Primeiros embarques no 3T 2026, *ramp* de volume no 4T; 150 parceiros de cadeia em Taiwan e 350+ fábricas em 30 países. A plataforma usa HBM4 e NVLink 6. O **backlog combinado Blackwell+Rubin é de ~US$ 500 bilhões** até o fim de 2026 (CFO Colette Kress), excluindo China e o *deal* OpenAI.

**Concorrência da AMD.** As linhas MI350/MI355X (CDNA 4, 288GB HBM3e, 8TB/s) entregam paridade aproximada com o B200 em inferência e vantagem de capacidade de memória. A MI400/MI450 "Helios" chega no 2S2026 com 432GB HBM4 (19,6 TB/s — ~1,6x a memória do GB200). O **ROCm 7** fechou parte da lacuna com o CUDA (AMD reivindica 3,5x de inferência vs. ROCm 6), mas ainda fica "anos, não meses" atrás. O *deal* com a OpenAI (6GW; potencialmente US$ 80–100 bilhões de receita até 2030, primeiro 1GW com MI450 no 2S2026) é a âncora estratégica. A **margem bruta da AMD (~54%)** versus ~75% da NVDA é a principal razão pela qual a AMD não recebe múltiplos estilo NVIDIA.

**Custom silicon dos hyperscalers.** A **Broadcom** é a maior beneficiária do movimento: o CEO Hock Tan projeta **~US$ 56 bilhões de receita de semicondutores de IA em FY2026** (quase triplicando). Clientes: Google (TPU v7 "Ironwood", co-design Broadcom/MediaTek, dual-sourcing para v8), Meta (MTIA; *deal* de US$ 35 bilhões com a Broadcom estendendo a arquitetura até 2029), OpenAI (ASICs custom a partir de 2026) e Anthropic (até 1 milhão de TPUs). AWS lançou o **Trainium3** (3nm) no re:Invent; a Anthropic opera cluster de 400 mil chips Trainium2. Microsoft Maia 100 teve dificuldade de escalar além de cargas internas de Copilot. **Marvell** projeta US$ 9–11 bilhões de receita de ASIC de IA em 2026 (Amazon, Microsoft), porém ~¼ da escala da Broadcom. **A ameaça é estrutural, porém multi-ano:** para hyperscalers com >100 mil aceleradores, os ASICs podem oferecer 30–50% menor TCO em *workloads* específicos. O *moat* do CUDA (4 milhões de desenvolvedores, 17 anos) protege sobretudo o mercado de *merchant chips* e treinamento de fronteira.

**Restrições de exportação à China.** Em abril/2025, o governo dos EUA passou a exigir licença para o H20, levando a NVIDIA a um *charge* de US$ 4,5 bilhões no 1T FY26 (de uma estimativa inicial de US$ 5,5 bilhões) associado a excesso de estoque e obrigações de compra de H20, e à incapacidade de embarcar ~US$ 2,5 bilhões de receita naquele trimestre. No 2T FY26, a empresa guiou **~US$ 8,0 bilhões de receita perdida** ("This outlook reflects a loss in H20 revenue of approximately $8.0 billion") e registrou **zero vendas de H20 para clientes da China**. Em dez/2025, a administração Trump aprovou condicionalmente o H200 para a China (com **taxa de 25% da receita ao governo dos EUA** e aprovação caso a caso), mas, até o reporte mais recente, **nenhuma receita foi realizada** — o governo chinês desencoraja compras, empurrando para chips domésticos. O 10-Q confirma: "No shipments of Data Center Hopper products to China occurred during the quarter, compared with $4.6 billion in the first quarter of fiscal year 2026." A Huawei Ascend 910C (~60% do desempenho real do H100) tem produção alvo de ~600 mil unidades em 2026 (até ~1,6 milhão de dies). A participação da NVIDIA em vendas novas avançadas na China caiu de ~95% para ~zero, embora dados da IDC mostrem ~55% do *fluxo total* de 2025 (incluindo estoques pré-restrição).

**Moat de software, networking e sistemas.** O ecossistema combina **CUDA** (default de treinamento), networking (NVLink, InfiniBand pós-aquisição da Mellanox, Spectrum-X Ethernet) e sistemas *full-stack* (NVL72, racks, DGX Cloud). O **networking cresceu 263% a/a no 4T FY26 (US$ 11 bilhões)**. A estratégia de "fábricas de IA" verticalmente integradas aumenta o *lock-in* e o *attach rate*.

### (b) Principais Riscos para os Próximos 12 Meses

1. **Digestão/desaceleração de capex dos hyperscalers.** Segundo o Goldman Sachs (compilado por Yahoo Finance, abr/2026): "Google, Amazon, Microsoft, and Meta alone collectively plan to allocate $725 billion to capital expenditures in 2026 — up a staggering 77% from last year's already record-breaking $410 billion." Breakdown: Amazon ~US$ 200 bi, Microsoft ~US$ 190 bi, Alphabet US$ 175–185 bi, Meta US$ 115–135 bi. **Sinais mistos:** as ações da Meta caíram 9,25% após elevar o *guidance*; analistas alertam para queda de FCF (Amazon pode ficar negativo em 2026). Brent Thill (Jefferies) afirmou que "the bear thesis is garbage", mas o consenso reconhece que o limite vinculante migrou de chips para **eletricidade**.
2. **Concentração de clientes.** Dois clientes representaram **39% da receita** (Cliente A: 23%; Cliente B: 16%) no 2T FY26 — ante 25% no ano anterior; quatro clientes somaram ~61%. Risco material caso um grande comprador reduza pedidos.
3. **"Circular financing" / relação NVIDIA-OpenAI.** O *deal* anunciado de US$ 100 bilhões (set/2025) foi reduzido a um investimento de **US$ 30 bilhões** (parte de rodada de US$ 110 bilhões a valuation de US$ 730 bilhões *pre-money*, com Amazon US$ 50 bi e SoftBank US$ 30 bi). Dan Ives (Wedbush — não "Wedbury") esclareceu que o investimento "will not exceed $100 billion", chamou-o de "validation moment" e disse que a revolução da IA está no "3rd inning, 1 out in a 9-inning game". Huang chamou rumores de atrito com a OpenAI de "nonsense". O backlog de US$ 500 bilhões **exclui** o trabalho relacionado à OpenAI.
4. **Cadeia de suprimento.** Dependência crítica da **TSMC** (CoWoS esgotado para 2026, ~60% da capacidade alocada à NVIDIA) e de **HBM** (SK Hynix com ~62% de share e fornecendo ~2/3 do HBM4 da NVIDIA; Micron e Samsung secundários). HBM3E está efetivamente esgotado para 2026. Qualquer atraso na transição 3nm ou no HBM4 cria vácuo competitivo.
5. **Geopolítico/regulatório.** China, antitruste, tarifas e iniciativas como o AI OVERWATCH Act (potencial veto do Congresso sobre exportações Blackwell).
6. **Margem.** Trajetória de margem bruta ~71–75%; os custos do *ramp* da Rubin e o crescimento de opex (GAAP +52% a/a, a US$ 7,6 bilhões no 1T FY27; compromissos de fornecimento subiram a US$ 119,0 bilhões) são pressões a monitorar.
7. **Bolha de IA / sustentabilidade do ROI.** O **MIT Project NANDA**, em "The GenAI Divide: State of AI in Business 2025" (jul/2025; baseado em 52 entrevistas, 153 respostas de líderes e 300 implementações), constatou: "Just 5% of integrated AI pilots are extracting millions in value, while the vast majority remain stuck with no measurable P&L impact" (US$ 30–40 bilhões gastos). Michael Burry expandiu *puts* contra NVDA, Palantir e Oracle; o Goldman comparou o ambiente a 1997. **Contraponto:** backlog de US$ 500 bilhões e FCF real de ~US$ 49 bilhões/trimestre sustentam a tese de que se trata de mudança estrutural, não apenas hype.

### (c) Situação de Valuation

| Métrica (jun/2026) | NVDA | Histórico NVDA | AMD | Broadcom (AVGO) | TSMC (TSM) |
|---|---|---|---|---|---|
| P/L *trailing* | ~30–35x | — | — | ~63–82x | ~36x |
| P/L *forward* | ~20–23x | — | ~27–28x | ~33–41x | ~24–27x |
| EV/EBITDA | ~29x | média 5a ~57x | — | ~44x | — |
| EV/Sales | ~22x | — | — | — | — |
| PEG | ~0,44 | — | ~0,4–0,5 | ~0,53 | — |

- **Múltiplos atuais:** P/L *trailing* ~30–35x (MacroTrends/StockAnalysis), forward ~20–23x (GuruFocus 22,57x; StockAnalysis 20,0x), EV/EBITDA ~29x (vs. média histórica de 5 anos ~57x e média de 20 anos ~37x), EV/Sales ~22x, PEG ~0,44 — todos **bem abaixo das próprias médias históricas** da NVIDIA, refletindo compressão de múltiplo enquanto os lucros disparam.
- **Vs. pares:** a NVDA negocia a **desconto vs. Broadcom e AMD em EV/EBITDA forward** e em P/L forward, apesar de gerar mais caixa, ter margem bruta superior (~75% vs. ~54% da AMD) e posição competitiva mais forte. A TSMC (~24–27x forward) é a mais barata da cadeia, mas carrega risco geopolítico de Taiwan.
- **Crescimento e consenso:** estimativa de EPS non-GAAP FY27 de ~US$ 8; receita do 2T FY27 estimada em ~US$ 91–93 bilhões. **68 analistas** com rating médio "Strong Buy"; preço-alvo médio ~US$ 270–310 (TipRanks ~US$ 309; ChartMill ~US$ 272; faixa de US$ 130–135 na baixa a US$ 500 na alta).
- **Conclusão:** a ação está **justa a barata** dado o crescimento. O múltiplo forward de ~20–23x para uma empresa crescendo 85% e com PEG <0,5 é difícil de classificar como caro em termos relativos. O risco real não é o múltiplo *atual*, mas sim a **sustentabilidade do crescimento**: o preço embute execução quase perfeita (conversão de 85% de crescimento atual em ~20% de CAGR de longo prazo sem perder margem nem múltiplo).

### (d) Bull Case e Bear Case

**Bull case (bem articulado):**
- **TAM gigante:** a gestão projeta US$ 3–4 trilhões de gasto em infraestrutura de IA até o fim da década.
- **Inferência como driver durável:** a IA *agentic* multiplica a demanda de compute ("easily 100 times more", segundo Huang); a Grace Blackwell é "o rei da inferência".
- **Sovereign AI:** >US$ 20 bilhões em FY26; *deals* na Arábia Saudita (HUMAIN, ~US$ 100 bilhões / 2.200 MW), Coreia do Sul (260 mil GPUs), Europa, UAE (Stargate), Reino Unido. A NVIDIA supre GPUs para 52% dos projetos de infraestrutura soberana rastreados.
- **Networking + software/recurring revenue + cadência anual** (que congela concorrentes) + novos mercados (robótica, automotivo — Uber 100 mil veículos a partir de 2027).
- **Visibilidade:** backlog de ~US$ 500 bilhões dá lastro à receita até 2027.

**Bear case (bem articulado):**
- **Comoditização de hardware** e perda de share para ASICs (de ~86% para ~75% no mercado amplo de aceleradores em 2026).
- **Compressão de margem** com *ramp* da Rubin e pressão competitiva de preço.
- **Estouro da bolha de capex:** se grandes empresas admitirem ROI fraco, "o sentimento muda da noite para o dia" — não falha técnica, mas "ROI reality check".
- **China estruturalmente perdida** (~zero em vendas novas avançadas).
- **Valuation absoluto esticado:** *market cap* de ~US$ 5 trilhões exige superar expectativas já elevadas; a ação já caiu mesmo com boas notícias.

**Cenários de preço explícitos (12 meses):**

| Cenário | Faixa de Preço | Premissas-chave |
|---|---|---|
| **Bear** | ~US$ 130–150 | Desaceleração material de capex de hyperscalers + aceleração de silício interno + novas restrições de exportação; compressão de múltiplo para ~15–18x sobre EPS reduzido. |
| **Base** | ~US$ 270–300 | Consenso dos analistas; P/L ~30x sobre EPS FY27 de ~US$ 8; execução da Rubin sem retorno relevante da China. |
| **Bull** | ~US$ 360–490 | Manutenção do múltiplo + execução da Rubin + retorno parcial da China (mercado de ~US$ 50 bilhões) + monetização de software. O modelo da TIKR aponta ~US$ 486 assumindo CAGR de receita de 20% e margem líquida de ~57%, sem exigir expansão de múltiplo. |

---

## Recommendations (Recomendações Acionáveis)

1. **Investidor de longo prazo:** o desconto de múltiplo (PEG <0,5, EV/EBITDA ~metade da média histórica) versus crescimento de 85% é raro e atraente. Estratégia escalonada: acumular em quedas, dimensionando posição para a volatilidade (beta ~2,2). **Benchmark de reversão:** margem bruta sustentadamente abaixo de 70%, ou revisão para baixo do capex dos hyperscalers nas próximas *earnings calls*.
2. **Gestão de risco / monitoramento contínuo:** acompanhar trimestralmente (a) *guidance* de capex de MSFT/GOOGL/AMZN/META; (b) *win rates* concretos da AMD MI400 com hyperscalers; (c) avanço de share dos ASICs (Broadcom/Marvell); (d) sinais de ROI corporativo real de IA (estudos como o do MIT NANDA).
3. **Gatilhos para reduzir exposição:** admissão pública de ROI fraco por grandes empresas; nova expansão de controles de exportação (ex.: Blackwell); perda de cliente âncora (dado o risco de 39% em 2 clientes); sinais de *inventory correction* na cadeia.
4. **Gatilhos para aumentar exposição:** reabertura efetiva da China (mercado endereçável de ~US$ 50 bilhões), aceleração de contratos de *sovereign AI*, e monetização crescente de software/serviços recorrentes (DGX Cloud, AI Enterprise).

---

## Caveats (Ressalvas)

- **Preço e múltiplos variam por fonte e data:** a ação oscilou entre ~US$ 200 e ~US$ 220 em junho/2026; métricas de P/L e EV/EBITDA divergem ligeiramente entre provedores (StockAnalysis, GuruFocus, MacroTrends, FinanceCharts).
- **Estimativas vs. dados realizados:** as participações no mercado amplo de aceleradores de IA, o TAM de US$ 3–4 trilhões, o backlog de US$ 500 bilhões e o mercado chinês de ~US$ 50 bilhões são **caracterizações da gestão ou projeções de analistas**, não dados auditados. A queda de share para ~75% em 2026 é projeção.
- **China:** as cifras de "95% para zero" (Huang, vendas novas avançadas) e "~55%" (IDC, fluxo total de 2025) medem coisas diferentes e não são contraditórias.
- **Fontes secundárias:** algumas estimativas de share derivam de agregadores (Silicon Analysts citando Mercury Research/SemiAnalysis) que não puderam ser rastreados até a publicação primária; tratá-las como estimativas atribuídas.
- **Não é recomendação de investimento.** Veja o disclaimer no topo.

---

## Referências / Bibliografia

1. NVIDIA Newsroom — "NVIDIA Announces Financial Results for Fourth Quarter and Fiscal 2026" (25/02/2026). https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2026
2. NVIDIA / SEC — "NVIDIA CORP Form 8-K – FY2026 (Q4)" (25/02/2026). https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000019/q4fy26pr.htm
3. NVIDIA / SEC — "NVIDIA CORP Form 8-K – Q1 FY2027" (20/05/2026). https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000051/q1fy27pr.htm
4. StockTitan — "Record $81.6B Q1 revenue as NVIDIA (NASDAQ: NVDA) boosts dividend" (20/05/2026). https://www.stocktitan.net/sec-filings/NVDA/8-k-nvidia-corp-reports-material-event-56086a88bbb4.html
5. CNBC — "Nvidia (NVDA) Q1 2027 earnings report: Live updates" (20/05/2026). https://www.cnbc.com/2026/05/20/nvidia-nvda-earnings-report-q1-2027.html
6. CNBC — "Nvidia earnings takeaways: Data center revenue nearly doubles, report is strong but stock slides" (20/05/2026). https://www.cnbc.com/2026/05/20/nvidia-nvda-earnings-report-q1-2027.html
7. TIKR — "NVIDIA Q1 2027 Earnings: $81.6B Revenue and Three Straight Quarters of Acceleration" (22/05/2026). https://www.tikr.com/blog/nvidia-q1-2027-earnings-81-6b-revenue-and-three-straight-quarters-of-acceleration
8. TIKR — "NVIDIA Stock Pulls Back Before May 20 Earnings…" (mai/2026). https://www.tikr.com/blog/nvidia-stock-pulls-back-before-may-20-earnings-heres-what-the-1-trillion-demand-story-still-needs-to-prove
9. INDmoney — "Nvidia Stock After Earnings: Nvidia Reports $81.6B Revenue, Raises Dividend 25x" (mai/2026). https://www.indmoney.com/blog/us-stocks/nvidia-stock-q1-fy27-earnings-81b-revenue-25x-dividend
10. Yahoo Finance — "Nvidia posts record $215 billion annual revenue…" (25/02/2026). https://finance.yahoo.com/news/nvidia-posts-record-215-billion-102845670.html
11. ServeTheHome — "NVIDIA Reports Q4'FY2026 Earnings…" (25/02/2026). https://www.servethehome.com/nvidia-reports-q4-fy2026-earnings-data-center-and-proviz-drive-revenue-records/
12. Futurum — "NVIDIA Q3 FY 2026 Earnings: Record Data Center Revenue" (nov/2025). https://futurumgroup.com/insights/nvidia-q3-fy-2026-record-data-center-revenue-higher-q4-guide/
13. Futurum — "NVIDIA Q2 FY 2026 Earnings: Networking Steals the Spotlight" (ago/2025). https://futurumgroup.com/insights/nvidia-q2-fy-2026-earnings-networking-steals-the-spotlight/
14. NVIDIA / SEC — "NVIDIA Announces Financial Results for First Quarter Fiscal 2026" (28/05/2025). https://www.sec.gov/Archives/edgar/data/1045810/000104581025000115/q1fy26pr.htm
15. NVIDIA Newsroom — "NVIDIA Announces Financial Results for First Quarter Fiscal 2026" (28/05/2025). https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-first-quarter-fiscal-2026
16. NVIDIA / SEC — "NVIDIA CORP Form 8-K – Q2 FY2026" (27/08/2025). https://www.sec.gov/Archives/edgar/data/0001045810/000104581025000207/q2fy26pr.htm
17. Bullfincher — "NVIDIA Corporation Revenue Breakdown By Segment". https://bullfincher.io/companies/nvidia-corporation/revenue-by-segment
18. NVIDIA Newsroom — "NVIDIA Vera Rubin Ramps Into Full Production…" (31/05/2026). https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Vera-Rubin-Ramps-Into-Full-Production-to-Power-Agentic-AI-Factories-Worldwide/default.aspx
19. HPCwire — "NVIDIA Vera Rubin Ramps into Full Production…" (01/06/2026). https://www.hpcwire.com/off-the-wire/nvidia-vera-rubin-ramps-into-full-production-to-power-agentic-ai-factories-worldwide/
20. SiliconANGLE — "Nvidia ramps up production of Vera Rubin…" (01/06/2026). https://siliconangle.com/2026/06/01/nvidia-ramps-production-vera-rubin-foundation-next-generation-ai-factories/
21. Wccftech — "NVIDIA Confirms Vera Rubin Launch In Q3 With Volume Ramp by Q4…" (mai/2026). https://wccftech.com/nvidia-confirms-vera-rubin-launch-in-q3-volume-ramp-q4-blackwell-continues-to-see-massive-demand/
22. ServeTheHome — "NVIDIA Computex 2026 News Bytes: Vera Rubin Now In Production…" (jun/2026). https://www.servethehome.com/nvidia-computex-2026-news-bytes-vera-rubin-now-in-production-dgx-station-gets-windows/
23. Silicon Analysts — "AMD vs NVIDIA AI GPU Market Share 2026: MI350X vs B200…" (abr/2026). https://siliconanalysts.com/analysis/amd-vs-nvidia-ai-gpu-market-share-2026
24. Introl — "AMD MI350 GPU Competition" (dez/2025). https://introl.com/blog/amd-mi350-gpu-competition-nvidia-enterprise-infrastructure
25. Investing.com — "AMD's SWOT analysis: How OpenAI deal reshapes stock's future in AI race". https://www.investing.com/news/swot-analysis/-amds-swot-analysis-how-openai-deal-reshapes-stocks-future-in-ai-race-93CH-4317936
26. Network World — "AMD steps up AI competition with Instinct MI350 chips, rack-scale platform". https://www.networkworld.com/article/4006570/amd-steps-up-ai-competition-with-instinct-mi350-chips-rack-scale-platform.html
27. Tech Insider — "AMD MI400 Series: $7.2B AI GPU Challenging Nvidia [2026]". https://tech-insider.org/amd-mi400-series-ai-gpu-data-center-2026/
28. AMD / SEC — "Building the Compute Foundation for the AI Era — 2025 Annual Report". https://ir.amd.com/financial-information/sec-filings/content/0001193125-26-129106/0001193125-26-129106.pdf
29. Swotpal — "AMD SWOT Analysis 2026: Q1 Earnings Preview…" (mai/2026). https://swotpal.com/blog/amd-swot-analysis-2026
30. Tom's Hardware — "The custom AI ASIC state of play (May 2026)…" (mai/2026). https://www.tomshardware.com/tech-industry/semiconductors/custom-ai-asics-examined-from-broadcom-to-mtia
31. Tech Insider — "Google TPU 8t and 8i: 121 Exaflops, $21B Nvidia Challenge". https://tech-insider.org/google-tpu-8t-8i-broadcom-mediatek-nvidia-2026/
32. Tech Insider — "Broadcom AI Revenue Surges 106%: Custom Chip Strategy 2026". https://tech-insider.org/broadcom-ai-revenue-custom-chips-2026/
33. Tech Times — "NVIDIA Is Not the Only AI Chip Winner: Broadcom Forecasts $56 Billion…" (05/06/2026). https://www.techtimes.com/articles/317846/20260605/nvidia-not-only-ai-chip-winner-broadcom-forecasts-56-billion-custom-silicon-demand-surges.htm
34. CNBC — "Nvidia sales are 'off the charts,' but Google, Amazon and others now make their own custom AI chips" (21/11/2025). https://www.cnbc.com/2025/11/21/nvidia-gpus-google-tpus-aws-trainium-comparing-the-top-ai-chips.html
35. Hashrate Index — "Inside the Custom AI Chip Race: Google, AWS, Microsoft, Meta, OpenAI". https://hashrateindex.com/blog/hyperscaler-ai-asic-market-report-part-1/
36. Computer Weekly — "AI chip restrictions limit Nvidia H20 China exports" (abr/2025). https://www.computerweekly.com/news/366622857/AI-chip-restrictions-limit-Nvidia-H20-China-exports
37. Introl — "BIS H200 Export Policy Shift & AI OVERWATCH Act" (2026). https://introl.com/blog/bis-h200-china-export-policy-ai-overwatch-act-2026
38. Council on Foreign Relations — "China's AI Chip Deficit: Why Huawei Can't Catch Nvidia…". https://www.cfr.org/articles/chinas-ai-chip-deficit-why-huawei-cant-catch-nvidia-and-us-export-controls-should-remain
39. Tom's Hardware — "White House U-turn on Nvidia H200 AI accelerator exports…". https://www.tomshardware.com/tech-industry/white-house-u-turn-on-nvidia-h200-ai-accelerator-exports-down-to-huaweis-powerful-new-ascend-chips-report-claims-u-s-committed-to-dominance-of-the-american-tech-stack
40. Tom's Hardware — "Nvidia prepares shipment of 82,000 AI GPUs to China as chip war lines blur". https://www.tomshardware.com/tech-industry/semiconductors/nvidia-prepares-h200-shipments-to-china-as-chip-war-lines-blur
41. Tom's Hardware — "Nvidia market share in China falls to less than 60%…" (abr/2026). https://www.tomshardware.com/tech-industry/nvidia-market-share-in-china-falls-to-less-than-60-percent-chinese-chip-makers-deliver-1-65-million-ai-gpus-as-the-government-pushes-data-centers-to-use-domestic-chips
42. Tom's Hardware — "Jensen says Nvidia's China AI GPU market share has plummeted from 95% to zero". https://www.tomshardware.com/tech-industry/jensen-huang-says-nvidia-china-market-share-has-fallen-to-zero
43. South China Morning Post — "Nvidia chief holds onto hope for policy change as China market share drops to 0 from 95%". https://www.scmp.com/tech/article/3329292/nvidia-chief-holds-hope-policy-change-china-market-share-drops-0-95
44. Built In — "Trump Lifted the AI Chip Ban on China, Clearing Nvidia and AMD to Resume Sales: Now What?". https://builtin.com/articles/trump-lifts-ai-chip-ban-china-nvidia
45. TechCrunch — "Nvidia expects to lose billions in revenue due to H20 chip licensing requirements" (28/05/2025). https://techcrunch.com/2025/05/28/nvidia-expects-to-lose-billions-in-revenue-due-to-h20-chip-licensing-requirements/
46. Yahoo Finance / Goldman Sachs — "Meta, Microsoft, Amazon, and Alphabet are about to spend a shocking amount of money…" (abr/2026). https://finance.yahoo.com/sectors/technology/article/meta-microsoft-amazon-and-alphabet-are-about-to-spend-a-shocking-amount-of-money-to-dominate-the-ai-era-115359575.html
47. Yahoo Finance — "Hyperscalers Hit $700 Billion in 2026 AI Spending Plans" (2026). https://finance.yahoo.com/sectors/technology/articles/hyperscalers-hit-700-billion-2026-111243744.html
48. Tom's Hardware — "Google, Microsoft, Meta, and Amazon capex spending to hit $725 billion in 2026…". https://www.tomshardware.com/tech-industry/big-tech/big-techs-ai-spending-plans-reach-725-billion
49. Futurum — "AI Capex 2026: The $690B Infrastructure Sprint". https://futurumgroup.com/insights/ai-capex-2026-the-690b-infrastructure-sprint/
50. CNBC — "Tech AI spending approaches $700 billion in 2026, cash taking big hit" (06/02/2026). https://www.cnbc.com/2026/02/06/google-microsoft-meta-amazon-ai-cash.html
51. CNBC — "Nvidia shares are down after a report that its OpenAI investment stalled…" (02/02/2026). https://www.cnbc.com/2026/02/02/nvidia-stock-price-openai-funding.html
52. Gizmodo — "The $100 Billion OpenAI-Nvidia Deal Is Not Happening". https://gizmodo.com/the-100-billion-openai-nvidia-deal-is-not-happening-2000729749
53. Tech Times — "NVIDIA OpenAI Investment Shrinks From $100B to $30B…" (05/06/2026). https://www.techtimes.com/articles/317839/20260605/nvidia-openai-investment-shrinks-100b-30b-compute-lock-war-continues.htm
54. Yahoo Finance — "Nvidia Says $100 Billion OpenAI Investment Framework Not Yet Finalized". https://finance.yahoo.com/news/nvidia-says-100-billion-openai-183732361.html
55. Bloomberg — "AI Circular Deals: How Microsoft, OpenAI and Nvidia Keep Paying Each Other" (jan/2026). https://www.bloomberg.com/graphics/2026-ai-circular-deals/
56. Silicon Analysts — "TSMC Foundry Allocation 2026: CoWoS Sold Out, 2nm Booked…" (jun/2026). https://siliconanalysts.com/analysis/foundry-allocation-status-q1-2026
57. UncoverAlpha — "2026 AI landscape: who benefits the most?". https://www.uncoveralpha.com/p/2026-ai-landscape-who-benefits-the
58. Fusionww — "Inside the AI Bottleneck: CoWoS, HBM, and 2–3nm Capacity Constraints Through 2027". https://info.fusionww.com/blog/inside-the-ai-bottleneck-cowos-hbm-and-2-3nm-capacity-constraints-through-2027
59. DIGITIMES — "SK Hynix targets February HBM4 ramp-up with TSMC, ships final samples to Nvidia" (26/12/2025). https://www.digitimes.com/news/a20251226PD215/sk-hynix-nvidia-hbm4-tsmc-production.html
60. Roic.ai — "NVIDIA's $500 Billion AI Chip Pipeline Excludes OpenAI Deal…" (02/12/2025). https://www.roic.ai/news/nvidias-500-billion-ai-chip-pipeline-excludes-openai-deal-signaling-even-greater-revenue-ahead-12-02-2025
61. Investing.com — "Nvidia: GPU Order Backlog Signals Long Multi Year Cycle". https://www.investing.com/analysis/nvidia-gpu-order-backlog-signals-long-multi-year-cycle-200670726
62. MacroTrends — "NVIDIA PE Ratio 2012-2026 | NVDA". https://www.macrotrends.net/stocks/charts/NVDA/nvidia/pe-ratio
63. StockAnalysis — "NVIDIA (NVDA) Statistics & Valuation". https://stockanalysis.com/stocks/nvda/statistics/
64. GuruFocus — "NVIDIA Forward PE Ratio: 22.57 | Possible Value Trap" (23/06/2026). https://www.gurufocus.com/term/forward-pe-ratio/NVDA
65. FinanceCharts — "NVIDIA (NVDA) EV to EBITDA Ratio – Current & Historical Data (Jun 2026)". https://www.financecharts.com/stocks/NVDA/value/ev-to-ebitda
66. FinanceCharts — "NVIDIA (NVDA) EV to Sales Ratio (Jun 2026)". https://www.financecharts.com/stocks/NVDA/value/ev-to-sales
67. TipRanks — "Nvidia Corporation (NVDA) Stock Forecast, Price Targets and Analysts Predictions". https://www.tipranks.com/stocks/nvda/forecast
68. ChartMill — "NVDA Forecast, Price Target & Analyst Ratings". https://www.chartmill.com/stock/quote/NVDA/analyst-ratings
69. WEEX — "NVIDIA Stock Price Forecast: 2026 Targets and How to Trade NVDA" (15/06/2026). https://www.weex.com/wiki/article/nvidia-stock-price-forecast-2026-targets-and-how-to-trade-nvda-fgtvo2lzwvvtks6zz1yrxabh
70. 24/7 Wall St. — "TSM vs Broadcom: Both Nearing 52-Week High, Only One is a Buy" (29/05/2026). https://247wallst.com/investing/2026/05/29/tsm-vs-broadcom-both-nearing-52-week-high-only-one-is-a-buy/
71. Gotrade — "NVIDIA vs TSMC vs Broadcom: Which AI Chip Stock Looks Best in 2026?". https://www.heygotrade.com/en/blog/ai-semiconductor-stocks-2026-nvidia-tsmc-broadcom/
72. GuruFocus — "BROADCOM Forward PE Ratio: 32.82 | Modestly Overvalued" (25/06/2026). https://www.gurufocus.com/term/forward-pe-ratio/AVGO
73. StockAnalysis — "Broadcom (AVGO) Statistics & Valuation". https://stockanalysis.com/stocks/avgo/statistics/
74. Deep Research Global — "Nvidia – Company Analysis and Outlook Report (2026)". https://www.deepresearchglobal.com/p/nvidia-company-analysis-outlook-report
75. CNBC — "Nvidia's top two mystery customers made up 39% of the chipmaker's Q2 revenue" (28/08/2025). https://www.cnbc.com/2025/08/28/nvidias-top-two-mystery-customers-made-up-39percent-of-its-q2-revenue-.html
76. TechCrunch — "Nvidia says two mystery customers accounted for 39% of Q2 revenue" (30/08/2025). https://techcrunch.com/2025/08/30/nvidia-says-two-mystery-customers-accounted-for-39-of-q2-revenue/
77. MIT Project NANDA — "The GenAI Divide: State of AI in Business 2025" (jul/2025).
78. MIT Technology Review — "What even is the AI bubble?" (15/12/2025). https://www.technologyreview.com/2025/12/15/1129183/what-even-is-the-ai-bubble/
79. Coin Edition — "Michael Burry Expands AI Short as 2026 IPO Wave Tests Bubble Warning". https://coinedition.com/michael-burry-expands-ai-short-as-2026-ipo-wave-tests-bubble-warning/
80. IT Pro — "What might cause the 'AI bubble' to burst…". https://www.itpro.com/technology/artificial-intelligence/might-cause-ai-bubble-burst-what-impact-on-business-world
81. Yahoo Finance — "Nvidia steps up South Korea AI push with 260,000-chip rollout". https://finance.yahoo.com/news/nvidia-steps-up-south-korea-ai-push-with-260000-chip-rollout-060026207.html
82. NVIDIA — "National Transformation With Sovereign AI". https://www.nvidia.com/en-us/industries/government/global-public-sector/
83. The National — "What the UAE's mega-deal with Nvidia means for its AI sovereignty" (27/03/2026). https://www.thenationalnews.com/business/2026/03/27/what-the-uaes-mega-deal-with-nvidia-means-for-its-ai-sovereignty/
84. CNAS Reports — "Sovereign AI Index" (dados de jan/2026). https://interactives.cnas.org/reports/sovereign-ai-index/
85. RoboForex — "NVIDIA Corporation (NVDA) stock analysis and forecast for 2026". https://roboforex.com/beginners/analytics/forex-forecast/stocks/stocks-forecast-nvidia-nvda/
86. Crypto Briefing — "Nvidia's profit margins projected to remain above 70% through 2030". https://cryptobriefing.com/nvidia-profit-margins-above-70-percent-2030/
87. Computer Weekly — "Nvidia takes $4.5bn hit due to export restrictions" (mai/2025). https://www.computerweekly.com/news/366625005/Nvidia-takes-45bn-hit-due-export-restrictions