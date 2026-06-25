# Infraestrutura de Energia para Data Centers de IA — Tese de Investimento e Cadeia de Valor Completa

**Data-base: 25 de junho de 2026** · Foco: players **listados nos EUA**, elo por elo da cadeia.

> Nota metodológica: relatório construído a partir de ~21 buscas web e leitura de fontes primárias e setoriais (releases corporativos, SEC, Bloomberg, Reuters/Fortune, Utility Dive, Power Engineering, Deloitte etc.). Todas as afirmações factuais estão referenciadas na seção **Fontes**. Onde houve divergência entre fontes (ex.: valor do deal Constellation–Calpine, market cap da Oklo), os números são apresentados com a fonte e a data específica. Empresas estrangeiras citadas como concorrentes (Schneider, ABB, Siemens Energy, Mitsubishi, Prysmian) **não são listadas nos EUA** e aparecem apenas como contexto competitivo — o foco da tese são os tickers americanos.

---

## 1. A Tese em Uma Frase

O gargalo do ciclo de IA deixou de ser GPU e passou a ser **energia**: não há capital nem chips suficientes parados — falta eletricidade, transformadores, turbinas e capacidade de refrigerar racks cada vez mais densos. A tese de "infraestrutura de energia para IA" monetiza esse gargalo ao longo de toda a cadeia física que liga a usina ao chip ("grid-to-chip").

**Dimensão do mercado (números-âncora):**
- Amazon, Google, Meta e Microsoft gastam juntas cerca de **US$ 400 bi/ano** em infraestrutura de data center de IA; o capex agregado de IA/data center em 2026 deve se aproximar de **US$ 700 bi**, salto de ~81% sobre 2025 [1].
- A demanda elétrica de data centers nos EUA é projetada em ~**750 TWh até 2030**, com a capacidade saindo de ~32 GW para ~**95 GW** (alta de ~197% entre 2025 e 2030); a fatia dos data centers no consumo elétrico americano dobra de ~6% para ~11% [1].
- **Energia — não capital — é a principal restrição.** Interconexões de grid podem levar até 4 anos; construir a infraestrutura elétrica completa pode levar ~8 anos, o que torna soluções *Bring-Your-Own-Power* (BYOP) e *behind-the-meter* (BTM) cada vez mais atraentes [1].
- O gargalo já trava obras: segundo a Bloomberg (abr/2026), **mais da metade** dos data centers planejados nos EUA para o ano devem ser adiados ou cancelados — não por falta de dinheiro ou terreno, mas por escassez de **transformadores e equipamento elétrico** [10][11].

Por que isso vira tese de equity: lead times longos (turbinas 3–7 anos; transformadores até 4 anos) criam **pricing power** e **backlogs plurianuais** que dão visibilidade de receita rara em industrials — daí o re-rating violento de 2023–2026 [4][9][10].

---

## 2. Mapa da Cadeia de Valor (visão de alto nível)

```
GERAÇÃO ── TRANSMISSÃO/GRID ── EQUIP. ELÉTRICO ── DISTRIBUIÇÃO BTM ── COOLING ── CHIP
  │              │                   │                    │             │
IPPs         EPC de grid        Turbinas, trafos,     Switchgear,    Líquido/ar,
Nuclear      (linhas, subest.)  grid hardware         gensets,       CDUs, chillers
Gás          Cabos/condutores   (GEV, ETN, VRT)       fuel cells     (VRT, MOD, JCI...)
SMRs         (PWR, MYRG, MTZ)                          (BE, CAT, CMI)
Solar+BESS
  │
COMBUSTÍVEL: gás (pipelines WMB/KMI/ET) · urânio/enriquecimento (CCJ/LEU)
```

---

## 3. Elo 1 — Geração de Energia: Independent Power Producers (IPPs)

Tornaram-se o "veículo default" da tese de *AI power* em equity. Os três operam grandes frotas **nucleares**, assinaram *offtakes* diretos com hyperscalers em 2024–2025 e re-rataram fortemente [2][7].

| Ticker | Empresa | Por que está aqui / diferenciação | Dados concretos |
|---|---|---|---|
| **CEG** | Constellation Energy | Maior operadora **nuclear** dos EUA; após comprar a Calpine virou o **maior produtor privado de eletricidade** do país. Tese: baseload nuclear "carbon-free" sob contrato de 20 anos com hyperscalers. | Fechou a Calpine em **7/jan/2026**; frota combinada **~55 GW** (22 GW nuclear baseload; algumas fontes citam 32,4 GW de nuclear próprio + ~26 GW de gás da Calpine). Valor do deal divergente entre fontes: ~US$ 16,4 bi em ações + caixa / ~US$ 26,6 bi total com dívida assumida. PPAs com Microsoft, Meta e CyrusOne [2][7][14]. Restart de Three Mile Island ("Crane Clean Energy Center", 835 MW) dedicado à Microsoft por 20 anos; waiver do PJM aprovado pela FERC em 1/jun/2026; ~80% do staff contratado para restart em 2027 [15]. |
| **VST** | Vistra | Maior produtor de energia **não-regulado** dos EUA; frota ~50 GW com nuclear (Comanche Peak) + gás + renováveis. Diferencia-se pela escala merchant e contratos de longo prazo. | PPA de 20 anos com AWS de até 1.200 MW (Comanche Peak) e PPAs de 20 anos com Meta de 2.600+ MW; guidance 2026 de EBITDA ajustado de **US$ 6,8–7,6 bi** [2][6]. |
| **TLN** | Talen Energy | Pure-play nuclear/merchant com a usina **Susquehanna**; primeiro a fazer deal *behind-the-meter* com hyperscaler (Amazon). | Ampliou o PPA com a Amazon para **1.920 MW até 2042**; ação +66,6% em 12 meses [2][15]. |

**Dinâmica de consolidação:** analistas esperam que IPPs maiores (Vistra, Constellation, Talen) **adquiram desenvolvedores menores** para montar "mega-sites" que empacotam terra + energia + fibra [2].

> Outros nomes do elo (não aprofundados aqui por foco nas fontes): **NRG Energy (NRG)**, **PSEG (PEG)**.

---

## 4. Elo 2 — Utilities Reguladas (carga + grid)

Captam o crescimento de carga via base de ativos regulada (rate base), com pipelines de "large load" (data centers) que viraram o principal driver de capex.

| Ticker | Empresa | Por que está aqui / diferenciação | Dados concretos |
|---|---|---|---|
| **NEE** | NextEra Energy | Maior gerador de renováveis + nuclear regulado dos EUA; em fusão para criar a maior utility regulada do mundo. | Fusão all-stock com a Dominion anunciada em **18/mai/2026**, ~**US$ 66,8 bi** (enterprise value ~US$ 420 bi); combinada teria portfólio de 110 GW, podendo dobrar para ~260 GW até 2032, e pipeline de "large-load" de **>130 GW**. Acionistas NEE ficam com ~74,5% [12][13]. |
| **D** | Dominion Energy | Dona do mercado da Virgínia ("data center alley" nº 1 do mundo); alvo da NEE. | Pipeline contratado de data centers **~51 GW**; vendeu 4% mais energia YoY na Virgínia no 1T26 [13]. |
| **EXC** | Exelon | Maior número de clientes de utility regulada dos EUA; líder também em capacidade nuclear regulada (referência citada na análise da fusão NEE-D) [13]. | — |
| **AEP / PPL** | American Electric Power / PPL | Grandes backlogs de interconexão de data center; expostas a transmissão. | Backlogs de data center de **56 GW (AEP)** e **29 GW (PPL)** [13]. |
| **SO** | Southern Company | Utility do Sudeste (Geórgia) com forte crescimento de carga de data center; operadora nuclear (Vogtle). | Citada no outlook de utilities como beneficiária de carga de data center [2]. |

---

## 5. Elo 3 — Transmissão / Grid e Construção (EPC)

São as "picks-and-shovels" da expansão do grid: linhas, subestações, interconexões e o trabalho elétrico/mecânico dentro do data center. Modelo de longo ciclo com backlogs recordes.

| Ticker | Empresa | Por que está aqui / diferenciação | Dados concretos |
|---|---|---|---|
| **PWR** | Quanta Services | Maior EPC de energia elétrica dos EUA (linhas de transmissão, subestações, interconexões). A exposição a data center virou catalisador de crescimento. | 1T26: receita **US$ 7,87 bi** (+26,3% YoY), backlog recorde **~US$ 48,5 bi**; metas 2030 de EPS ajustado **US$ 21,60–26,75** e receita US$ 44–49 bi [3]. |
| **MTZ** | MasTec | Infraestrutura de energia/transmissão; beneficiária do capex de utilities. | Citada com Quanta/EMCOR como exposta a backlog crescente e visibilidade plurianual [3]. |
| **MYRG** | MYR Group | Pure-play em construção elétrica T&D e instalações comerciais/industriais; alavancada à expansão de grid para IA. | Ação disparou em mai/2026 junto a pares; "fortemente exposta à expansão do grid elétrico que IA demanda" [3]. |
| **EME** | EMCOR Group | Construção mecânica e elétrica; instala/mantém energia elétrica, HVAC e sistemas de missão crítica em data centers. | Beneficiária do mesmo ciclo de capex; visibilidade de backlog [3]. |
| **FIX** | Comfort Systems USA | MEP (mechanical/electrical/plumbing) — ponte entre EPC e cooling; backlog dobrou. | Backlog dobrou para **~US$ 12 bi**; negociava ~10% abaixo da máxima [4]. |

> Adjacência de **cabos/condutores**: a italiana **Prysmian** (não listada nos EUA) comprou a americana **Encore Wire** e agora controla ~1/3 da produção norte-americana de fio/cabo de cobre e alumínio, com nova fábrica no Texas (2027) — relevante como contexto de gargalo de cobre, mas sem ticker dos EUA puro nesse nicho [21][22].

---

## 6. Elo 4 — Equipamentos Elétricos (turbinas, trafos, switchgear, grid hardware)

O coração da tese de pricing power: três fabricantes globais de turbinas a gás de grande porte e um oligopólio de equipamento de distribuição com lead times explodindo.

### 6.1 Geração de equipamento / grid hardware / turbinas

| Ticker | Empresa | Por que está aqui / diferenciação | Dados concretos |
|---|---|---|---|
| **GEV** | GE Vernova | O player mais central da cadeia: turbinas a gás de grande porte **+ transformadores (via Prolec) + grid solutions + nuclear (BWRX SMR) + storage**. Cobre quase toda a coluna. | Backlog total subiu de US$ 116 bi (spin) para **~US$ 163 bi** (incl. ~US$ 87 bi em serviços); +US$ 13,0 bi sequencial no 1T26. Backlog de turbinas a gás + reservas de slot cresceu de **83 para 100 GW**, com meta de **≥110 GW** no fim de 2026. **Pedidos de eletrificação ligados a data center no 1T26 superaram TODO o ano de 2025** (~US$ 2,4 bi no trimestre). ~1/3 das reservas de turbina ligadas direta/indiretamente a IA/hyperscalers; lead time ~3 anos, slots de 2030 majoritariamente vendidos [3][4][9][10]. |

> **Concorrentes estrangeiros em turbinas** (não listados nos EUA): **Siemens Energy** (order book recorde ~€136 bi) e **Mitsubishi Heavy Industries** (slots cheios para 2027–2028). Só três fabricantes conseguem produzir turbinas de grande porte; esperas de **5 a 7 anos** dependendo do modelo [9].

### 6.2 Distribuição / switchgear / power management

| Ticker | Empresa | Por que está aqui / diferenciação | Dados concretos |
|---|---|---|---|
| **ETN** | Eaton | Líder em power management/distribuição (switchgear, trafos) sob medida para data center; investindo centenas de milhões em novas fábricas de trafo/switchgear nos EUA. | 1T26: vendas +17% (orgânico +10%); **backlog do segmento Electrical +48% YoY**; pedidos de data center na Electrical Americas **+~240%** e receita **+~50%** YoY; guidance de crescimento orgânico 2026 **elevado de 8% para 10%** [16]. |
| **VRT** | Vertiv | Pure-play do *physical layer* (power + cooling); ver também Elo 5. Entrou no S&P 500 em mar/2026. | Backlog **>US$ 15 bi** (book-to-bill ~2,9x no 4T25, pedidos +252% YoY); guidance 2026 elevado para **US$ 13,5–14,0 bi** (~30% crescimento orgânico, ~51% de crescimento de lucro) [4][20]. |
| **POWL** | Powell Industries | Switchgear de média/alta tensão e *behind-the-meter*; small cap alavancada a data center. | 2T FY26: receita US$ 297 mi (+6%), **pedidos US$ 490 mi (+97%)**, backlog US$ 1,8 bi (+33%); ganhou pedido recorde **>US$ 400 mi** para geração on-site BTM de mega data center; data center = ~15% do backlog [18]. |
| **NVT** | nVent Electric | Conexão/proteção elétrica + soluções de cooling líquido e a ar; papel mais amplo que HVAC puro. | Backlog recorde **US$ 2,6 bi**; pedidos orgânicos +~40% no 1T (puxados por IA); novos produtos de data center somaram **>20 p.p.** ao crescimento de vendas [4][18]. |
| **HUBB** | Hubbell | Componentes elétricos e de grid; reforçando exposição a data center via M&A. | Em mai/2026 anunciou compra da **NSI Industries por US$ 3,0 bi** para reforçar data center / infra de rede [18]. |

> **Concorrentes estrangeiros em equipamento elétrico/switchgear** (não listados nos EUA): **Schneider Electric** (líder, ~18% de share global), **ABB/Hitachi Energy**, **Siemens**. Schneider + Eaton + Siemens detêm >40% do mercado global de switchgear de data center [17].

**Gargalo de transformadores (driver da tese):** demanda de trafos de potência nos EUA +100% desde 2019; preços +~70% desde 2019; **lead times de até 4 anos** [10][11]. GE Vernova ficou dominante em trafos após comprar a **Prolec** e expande capacidade nos EUA [10].

---

## 7. Elo 5 — Refrigeração / Cooling

À medida que os racks de GPU ficam mais densos, o ar atinge o limite e o gasto migra para **líquido**: chillers, CDUs (coolant distribution units), trocadores de calor e plataformas térmicas integradas. Um dos temas "picks-and-shovels" mais quentes [4].

| Ticker | Empresa | Por que está aqui / diferenciação | Dados concretos |
|---|---|---|---|
| **VRT** | Vertiv | "Heavyweight" do cooling de IA — projeta power + cooling líquido que hyperscalers compram por rack. Pure-play do *physical layer*. | Ver §6.2: backlog >US$ 15 bi; crescimento de pedidos histórico; entrada no S&P 500 [4][20]. |
| **MOD** | Modine Manufacturing | Virando **pure-play de térmica de data center** (spin-off de outros ativos); contrato âncora gigante. | Contrato de chiller com hyperscaler de **US$ 4 bi (2027–2029)**; vendas de data center +31% sequencial no 3T FY26; carteira de pedidos ~5 anos; expectativa de **50–70% de crescimento anual** no negócio de data center [4]. |
| **JCI** | Johnson Controls | Líder em chillers/HVAC + serviço; motor de backlog que o "rótulo de ciclo HVAC" subestima. | Backlog recorde **US$ 20 bi**; Americas **US$ 14,9 bi (+32% YoY)**; pedidos de sistemas nas Américas **+84% YoY**; dois novos chillers para data center em 2026 [19]. |
| **TT** | Trane Technologies | Building/thermal management entrando em cooling líquido de IA via M&A. | Comprou a **LiquidStack** (cooling líquido) e ativos térmicos de data center da Stellar Energy (dez) [19]. |
| **CARR** | Carrier Global | HVAC com backlog crescente em building solutions e data center cooling. | Demanda robusta de cooling de data center e heat pumps na América do Norte e Europa (1T26) [19]. |
| **FIX** | Comfort Systems USA | Ver §5 — MEP que executa boa parte do cooling físico; backlog dobrou para ~US$ 12 bi [4]. |
| **NVT** | nVent Electric | Ver §6.2 — soluções de cooling líquido e a ar além de equipamento elétrico [4]. |

---

## 8. Elo 6 — Nuclear e SMRs

Dois sub-elos distintos: **(a)** nuclear operacional já gerando caixa (os IPPs do §3 + utilities) e **(b)** SMRs/microreatores pré-receita, opções de longo prazo com risco de execução elevado (receita real só no fim da década/2030s).

### 8.1 Nuclear operacional (já no §3/§4): CEG, VST, TLN, GEV (SMR BWRX-300)

### 8.2 SMRs e advanced reactors (pré-receita)

| Ticker | Empresa | Por que está aqui / diferenciação | Dados concretos |
|---|---|---|---|
| **OKLO** | Oklo | Reator rápido a sódio (Aurora, 15–75 MW) em modelo **build-own-operate** (vende energia, não reatores) + reciclagem de combustível; pipeline ancorado em hyperscalers. | Pipeline de clientes ~**14 GW** (Switch, Equinix, Meta); deal com Meta (jan/2026) para campus nuclear de **1,2 GW** em Ohio; aprovação de design criteria pela NRC em mai/2026; 1ª powerhouse comercial visada para **fim de 2027/início de 2028** (construtor: Kiewit). Market cap volátil: ~US$ 11,5 bi (22/mai) caindo a ~US$ 8,7 bi (16/jun/2026). **Sem receita até ~2028** [5][23]. |
| **SMR** | NuScale Power | Único design de SMR com **certificação da NRC** (módulo de 77 MWe); comercializa via parceiro ENTRA1. | Programa não-vinculante com a **TVA de até 6 GW**; primeiras usinas só entregam energia no fim da década; receita de reator real provavelmente só nos anos 2030. Consenso Zacks de receita 2026 ~US$ 91,1 mi (+202% YoY, base baixa) [5][23]. |
| **BWXT** | BWX Technologies | Diferente dos pré-receita: **já lucrativo** (Marinha dos EUA + componentes nucleares); desenvolve o SMR BANR (75 MWe, combustível TRISO) para data center. | Receita 2025 **US$ 3,19 bi (+18%)**, EPS +20%; SMR BANR voltado a aplicações de data center [24]. |
| **NNE** | Nano Nuclear Energy | Microreatores (pré-comercial), small cap especulativa. | Market cap citado ~US$ 1,2 bi; desenvolvedora de microreatores [5]. |
| **LTBR** | Lightbridge | Tecnologia de combustível nuclear avançado. | ~US$ 500 mi de market cap [5]. |

> **Engenharia/EPC nuclear:** **Fluor (FLR)** — controladora histórica e subcontratada de FEED da NuScale; exposição indireta a SMR [24].

### 8.3 Combustível nuclear / enriquecimento (HALEU)

| Ticker | Empresa | Por que está aqui / diferenciação | Dados concretos |
|---|---|---|---|
| **CCJ** | Cameco | Líder global em urânio com contratos de longo prazo; exposição "core" ao tema nuclear. | ~230 milhões de libras de urânio sob contratos de longo prazo [25]. |
| **LEU** | Centrus Energy | **Única enriquecedora comercial de urânio sediada nos EUA**; única produtora doméstica de **HALEU** (combustível de SMRs/advanced reactors). | Receita de HALEU +47%; **task order do DOE de US$ 900 mi (jan/2026)** para expandir a planta de Ohio, dentro de plano de US$ 2,7 bi do DOE para a cadeia doméstica de enriquecimento [25]. |

---

## 9. Elo 7 — Gás Natural (turbinas, gensets, fuel cells e pipelines)

Gás é a "ponte" pragmática: mais de **40%** da demanda de energia de data center é atendida por gás natural, e o BYOP/on-site com gás contorna filas de interconexão [8][26].

### 9.1 Geração on-site / behind-the-meter (gensets e fuel cells)

| Ticker | Empresa | Por que está aqui / diferenciação | Dados concretos |
|---|---|---|---|
| **CAT** | Caterpillar | Grandes motores recíprocos + turbinas para geração on-site; vendido até 2027. | Power Generation (dentro de Energy & Transportation) **US$ 2,817 bi no 1T26 (+41% YoY)**; vendas de power gen +48%; backlog total recorde **US$ 63 bi (+79% YoY)**; backlog de grandes motores recíprocos +3,5x desde jan/2024; vai **triplicar** capacidade de grandes motores; pedidos do 1T26 só entregam em 2028 [26]. |
| **CMI** | Cummins | Gensets para data center; demanda "supera expectativas". | Líder (com CAT) no mercado de geradores de data center; demanda continua acima do esperado [26]. |
| **BE** | Bloom Energy | **Fuel cells de óxido sólido (SOFC)** behind-the-meter — geração primária on-site que dribla a fila do grid. Diferencia-se de gensets de backup por ser geração contínua. | >1,5 GW de fuel cells em 1.200+ sites; deals com Equinix e Compass; **parceria de US$ 5 bi com a Brookfield** para acelerar capacidade para IA [8]. |
| **GNRC** | Generac | Backup power / gensets (exposição mais tangencial; foco histórico em standby) [8]. |

### 9.2 Combustível — pipelines/midstream (o gás chega como?)

| Ticker | Empresa | Por que está aqui / diferenciação | Dados concretos |
|---|---|---|---|
| **WMB** | Williams Companies | Maior surto de construção de pipeline em ~20 anos; está indo além de transportar gás — **constrói usinas a gás modulares no próprio site do data center**. | Portfólio de "power innovation" de **US$ 5,1 bi**; US$ 3,1 bi em dois projetos de power de data center (out/2025); **Project Socrates** (US$ 1,6 bi) com conclusão no 2S26 [8]. |
| **KMI** | Kinder Morgan | Maior rede de gás dos EUA; projetos diretos para power/data center + RNG. | **Creekside Lateral** (~11,2 mi, 42") para power/industrial/data center, in-service no 4T26; comprou 7 ativos de gás de aterro por US$ 135 mi (out/2025) para suprir RNG a data centers [8]. |
| **ET** | Energy Transfer | Resolve gargalos regionais no Texas com deals diretos. | Deal com Cloud Burst; pipeline **Hugh Brinson** ajudará a suprir gás para data centers da Oracle [8]. |

---

## 10. Elo 8 — Armazenamento (BESS) e Renováveis

Storage e solar entram como complemento de firmeza/24-7 carbon-free e para acelerar time-to-market sob "bring your own generation".

| Ticker | Empresa | Por que está aqui / diferenciação | Dados concretos |
|---|---|---|---|
| **TSLA** | Tesla (Tesla Energy/Megapack) | Líder norte-americano em BESS utility-scale; integração vertical (bateria + power electronics + software). | Benchmark de confiabilidade/velocidade de deploy; mercado BESS NA indo de US$ 10,03 bi (2025) a US$ 19,87 bi (2030) [27]. |
| **GEV** | GE Vernova | Combina turbinas + BESS + grid digital em "soluções integradas" para clientes de alta carga (data centers) [27]. |
| **FLNC** | Fluence Energy | Pure-play de storage utility-scale; moat em software (plataforma de bidding com IA em ~50 mercados). | Receita FY25 US$ 2,3 bi; guidance FY26 **US$ 3,2–3,6 bi** (~85% em backlog); pipeline US$ 30 bi crescendo ~30%/trimestre [27]. |
| **NEE / FSLR** | NextEra / First Solar | Solar+storage para hyperscalers via PPA físico e 24/7 CFE. | Meta + NextEra fecharam grande deal de solar+storage; EIA projeta **43,4 GW** de solar utility-scale novo em 2026 (+60% vs. 2025, recorde) [28]. |

> Nota: **First Solar (FSLR)** aparece como o fabricante de painéis americano "puro" exposto ao tema, mas não obtive dado específico de PPA dedicado a data center nesta rodada — incluído como adjacência, não como convicção sourced.

---

## 11. Síntese — Mapa "Quem Ganha o Quê"

| Elo da cadeia | Tickers (EUA) | Natureza do ganho |
|---|---|---|
| Geração / IPPs | **CEG, VST, TLN** (NRG, PEG) | Offtake nuclear/merchant de longo prazo com hyperscalers |
| Utilities reguladas | **NEE, D, EXC, AEP, PPL, SO** | Crescimento de rate base via carga de data center |
| Transmissão/EPC | **PWR, MTZ, MYRG, EME, FIX** | Backlog plurianual de construção de grid e MEP |
| Equip. elétrico/turbinas | **GEV, ETN, VRT, POWL, NVT, HUBB** | Pricing power por lead times e backlog |
| Cooling | **VRT, MOD, JCI, TT, CARR, FIX, NVT** | Migração para cooling líquido; contratos âncora |
| Nuclear operacional | **CEG, VST, TLN, GEV** | Caixa nuclear hoje |
| SMRs (opção LP) | **OKLO, SMR, BWXT, NNE, LTBR** (FLR) | Pipeline futuro; alto risco/execução |
| Combustível nuclear | **CCJ, LEU** | Urânio + HALEU doméstico |
| Gás on-site/BTM | **CAT, CMI, BE, GNRC** | Geração on-site driblando a fila do grid |
| Gás midstream | **WMB, KMI, ET** | Pipelines + usinas no site |
| Storage/Renováveis | **TSLA, GEV, FLNC, NEE, FSLR** | Firmeza/24-7 CFE e time-to-market |

---

## 12. Riscos e Pontos de Atenção da Tese

- **SMRs são opções, não fluxos de caixa:** OKLO/SMR/NNE não têm receita comercial até ~2028–2030s; volatilidade extrema (market cap da Oklo oscilou de ~US$ 11,5 bi para ~US$ 8,7 bi em ~3 semanas) [5][23].
- **Risco de cancelamento de demanda:** se >50% dos data centers planejados de fato atrasarem/cancelarem por falta de equipamento, parte do backlog precificado pode escorregar no tempo [10][11].
- **Concentração regulatória/M&A:** fusões gigantes (NEE-D; Constellation-Calpine) dependem de aprovação FERC/DOJ e de waivers do PJM, com oposição (o monitor de mercado do PJM se opôs ao waiver da Constellation) [12][13][14][15].
- **Affordability e backlash político:** utilities estão "divididas" sobre repassar custos de data center a consumidores residenciais — risco regulatório de tarifa [tema recorrente nas fontes 2 e 13].
- **Players estrangeiros dominam elos-chave:** em turbinas (Siemens Energy, Mitsubishi) e switchgear (Schneider, ABB), boa parte do market share não está em tickers dos EUA — exposição "pura" via American depositary/listas locais, não no escopo desta tese.

---

## Fontes

1. Yahoo Finance / "AI Data Centers Will Soon Consume as Much Power as Two-Thirds of All American Homes" — https://finance.yahoo.com/sectors/energy/articles/ai-data-centers-soon-consume-173000513.html ; Deloitte, "Can US infrastructure keep up with the AI economy?" — https://www.deloitte.com/us/en/insights/industry/power-and-utilities/data-center-infrastructure-artificial-intelligence.html ; Westside Construction Group, "The Data Center Power Crisis" (2026) — https://www.buildwcg.com/blog-posts/data-center-power-grid-construction-ai-infrastructure-2026
2. AOL / Yahoo Finance, "Vistra vs. Constellation: Which AI Power Stock Is the Better Buy Right Now?" — https://www.aol.com/articles/vistra-vs-constellation-ai-power-113004457.html ; Lambda Finance, "Vistra vs Constellation vs Talen: Best AI Power Stocks (2026)" — https://www.lambdafin.com/articles/vistra-vs-constellation-vs-talen ; Gabelli, "Utilities – U.S. Outlook" — https://gabelli.com/research/utilities-u-s-outlook/
3. Yahoo Finance / Globe and Mail / TradingView, "Is Quanta's Data Center Exposure Turning Into Its Growth Catalyst?" — https://finance.yahoo.com/sectors/energy/articles/quantas-data-center-exposure-turning-131500744.html ; StockStory, "MYR Group and Tutor Perini Shares Are Soaring" — https://stockstory.org/us/stocks/nasdaq/myrg/news/why-up-down/myr-group-and-tutor-perini-shares-are-soaring-what-you-need-to-know ; TIKR, "Quanta Services 5-Year Plan" — https://www.tikr.com/blog/quanta-services-just-unveiled-its-most-ambitious-5-year-plan-yet-heres-what-it-means-for-investors ; Motley Fool, "3 Electrical Infrastructure Stocks" — https://www.fool.com/investing/2026/05/13/3-electrical-infrastructure-stocks-with-shockingly/
4. VaaSBlock, "Vertiv, Eaton, Schneider 2026" — https://www.vaasblock.com/news/vertiv-data-center-cooling-power-equipment-ai-2026/ ; TickerSpark, "Top Data Center Cooling Stocks 2026" — https://tickerspark.ai/top-stocks/best-data-center-cooling-stocks ; Yahoo/AOL (IBD), "One AI Cooling Stock Is 10% Off Highs" — https://finance.yahoo.com/markets/stocks/articles/one-ai-cooling-stock-10-120400120.html ; Yahoo Finance, "Vertiv vs. Modine" — https://finance.yahoo.com/news/vertiv-vs-modine-stock-edge-133600659.html ; TIKR, "GE Vernova Power Backlog 2026" — https://www.tikr.com/blog/ge-vernova-rose-6-today-why-its-power-backlog-could-drive-more-upside-in-2026
5. IndexBox, "NuScale and Oklo: Nuclear Energy Stocks for AI-Driven Demand 2026" — https://www.indexbox.io/blog/nuclear-energy-stocks-nuscale-power-and-oklo-inc-as-long-term-investments/ ; exoswan, "Top Small Modular Reactor Stocks 2026" — https://exoswan.com/small-modular-reactor-stocks/ ; Motley Fool, "NuScale vs. Oklo (2026)" — https://www.fool.com/coverage/better-buy/2026/05/27/nuscale-power-vs-oklo-which-nuclear-stock-is-a-better-buy-in-2026/
6. Luminix, "Vistra Power: 50 GW Fleet, Nuclear PPAs & AI Data Center Strategy 2026" — https://www.useluminix.com/reports/market-research/vistra-company-overview-power-generation-fleet-ai-data-center-strategy-and-market-position-2026
7. Hart Energy, "Constellation Closes $16.4B Calpine Deal" — https://www.hartenergy.com/energy-market-transactions/he-constellation-closes-164b-calpine-deal/
8. Fortune, "Data centers and gas demand make boring pipelines great again" (11/abr/2026) — https://fortune.com/2026/04/11/data-centers-gas-demand-make-boring-pipelines-great-again/ ; ETF Trends, "Midstream Leans Into AI Data Center Boom" — https://www.etftrends.com/energy-infrastructure-content-hub/midstream-leans-ai-data-center-boom/ ; Natural Gas Intelligence, "Midstream Giant Williams Cautions…" — https://naturalgasintel.com/news/midstream-giant-williams-cautions-natural-gas-demand-could-further-outpace-pipeline-capacity/ ; Seeking Alpha, "Bloom Energy: Solving The AI Data Center Power Bottleneck" — https://seekingalpha.com/article/4862022-bloom-energy-solving-the-ai-data-center-power-bottleneck ; Data Center Knowledge, "Hydrogen's Hurdles, Fuel Cells' Rise" — https://www.datacenterknowledge.com/uptime/hydrogen-s-hurdles-fuel-cells-rise-in-data-center-power
9. Bloomberg, "Siemens Energy, Mitsubishi Struggle to Keep Up With AI-Driven Demand For Gas Turbines" — https://www.bloomberg.com/features/2025-bottlenecks-gas-turbines/ ; Power Engineering, "Data centers drive record surge in GE Vernova power equipment orders…" — https://www.power-eng.com/gas/turbines/data-centers-drive-record-surge-in-ge-vernova-power-equipment-orders-as-turbine-slots-tighten-through-2030/ ; Natural Gas Intelligence, "North America's Natural Gas Turbine Market Fired Up…" — https://naturalgasintel.com/news/north-americas-natural-gas-turbine-market-fired-up-as-multi-year-backlog-seen-persisting/
10. Energy News Beat, "More than half of the Data Centers may be delayed due to lack of transformers…" — https://energynewsbeat.co/ai/more-than-half-of-the-data-centers-may-be-delayed-due-to-lack-of-transformers-and-electrical-equipment-2/ ; Bloomberg via Yahoo, "Data Center Rush Spurs Earnings Windfall for Power-Gear Makers" — https://www.bloomberg.com/news/articles/2026-02-23/data-center-rush-spurs-earnings-windfall-for-power-gear-makers
11. pv magazine USA, "U.S. transformer market faces severe supply constraints as lead times extend to four years" (11/mai/2026) — https://pv-magazine-usa.com/2026/05/11/u-s-transformer-market-faces-severe-supply-constraints-as-lead-times-extend-to-four-years/ ; Power Magazine, "Transformers in 2026: Shortage, Scramble, or Self-Inflicted Crisis?" — https://www.powermag.com/transformers-in-2026-shortage-scramble-or-self-inflicted-crisis/
12. NextEra Energy Newsroom, "NextEra Energy and Dominion Energy to Combine…" (18/mai/2026) — https://newsroom.nexteraenergy.com/2026-05-18-NextEra-Energy-and-Dominion-Energy-to-Combine ; S&P Global, "Dominion, NextEra to merge in massive all-stock deal" — https://www.spglobal.com/market-intelligence/en/news-insights/articles/2026/5/update-dominion-nextera-to-merge-in-massive-all-stock-deal-101811279
13. Utility Dive, "Combined NextEra-Dominion would have 130-GW large-load pipeline" — https://www.utilitydive.com/news/nextera-dominion-merger-would-create-worlds-largest-regulated-electric-ut/820457/ ; Utility Dive, "2026 Q1 roundup: Utilities divided on data centers as affordability looms large" — https://www.utilitydive.com/news/2026-q1-earnings-utilities-data-centers-affordability/820079/ ; Washington Post, "Dominion-NextEra merger, fueled by AI data center demand…" — https://www.washingtonpost.com/business/2026/05/18/dominion-nextera-merger-fueled-by-ai-data-center-demand-would-create-huge-utility/
14. Constellation Energy, "Constellation Completes Calpine Transaction" (jan/2026) — https://www.constellationenergy.com/news/2026/01/constellation-completes-calpine-transaction-powering-americas-clean-energy-future.html ; Press Democrat, "Constellation Energy completes acquisition of Calpine" — https://www.pressdemocrat.com/2026/01/26/constellation-calpine-geysers-acquisition/
15. Utility Dive, "Constellation's Three Mile Island nuclear restart gets boost with FERC waiver" — https://www.utilitydive.com/news/constellation-three-mile-island-crane-nuclear-ferc-waiver/821836/ ; DataCenterDynamics, "Three Mile Island… Microsoft signs 20-year, 835MW AI data center PPA" — https://www.datacenterdynamics.com/en/news/three-mile-island-nuclear-power-plant-to-return-as-microsoft-signs-20-year-835mw-ai-data-center-ppa/ ; enkiAI, "Microsoft Nuclear 2026, 1,920 MW Amazon PPA" — https://enkiai.com/nuclear/microsoft-constellation-ai-data-centers/
16. Eaton, "Eaton Reports Record First Quarter 2026 Results… Raises 2026 Organic Growth Guidance to 10%" — https://www.eaton.com/us/en-us/company/news-insights/news-releases/2026/eaton-reports-record-first-quarter-2026-results.html ; Alphastreet, "Eaton (ETN) Posts Record Q1 Revenue as Electrical Backlog Surges 48%…" — https://news.alphastreet.com/eaton-etn-posts-record-q1-revenue-as-electrical-backlog-surges-48-on-data-center-demand/amp/
17. IntelMarketResearch, "Data Center Switchgear Market Outlook 2026-2034" — https://www.intelmarketresearch.com/data-center-switchgear-market-36548 ; MarketsandMarkets, "Top Companies in Data Center Power Market" — https://www.marketsandmarkets.com/ResearchInsight/data-center-power-market.asp ; Mordor Intelligence, "Data Center Power Companies" — https://www.mordorintelligence.com/industry-reports/global-data-center-power-market-industry/companies
18. Dealroom, "Powell Industries secures $400M+ data center order, Q2 revenues reach $297M" — https://app.dealroom.co/news/feed/powell-industries-secures-400m-data-center-order-q2-revenues-reach-297m ; Simply Wall St, "Why Powell Industries (POWL) Is Up 10.3%…" — https://simplywall.st/stocks/us/capital-goods/nasdaq-powl/powell-industries/news/why-powell-industries-powl-is-up-103-after-record-q2-backlog ; Yahoo/Globe and Mail, "Can AI Data Center Demand Accelerate nVent Electric's Revenue Growth?" — https://finance.yahoo.com/sectors/technology/articles/ai-data-center-demand-accelerate-145200907.html
19. Facilities Dive, "Johnson Controls sees 84% systems order growth in the Americas" — https://www.facilitiesdive.com/news/johnson-controls-sees-84-systems-order-growth-in-the-americas/811368/ ; Facilities Dive, "Data center cooling drives Johnson Controls growth" — https://www.facilitiesdive.com/news/data-center-cooling-drives-johnson-controls-growth/804990/ ; Facilities Dive, "LiquidStack buy gives Trane AI data center cooling exposure" — https://www.facilitiesdive.com/news/liquidstack-buy-gives-trane-ai-data-center-cooling-exposure/812053/ ; Ad-Hoc News, "Carrier Global highlights data center demand" — https://www.ad-hoc-news.de/boerse/news/ueberblick/carrier-global-highlights-data-center-demand-shares-tracked-against-hvac/69625068
20. Alphastreet, "Vertiv Holdings (NYSE:VRT) Extends 2026 Rally After 64% Surge…" — https://news.alphastreet.com/vertiv-holdings-nysevrt-extends-2026-rally-after-64-surge-ai-data-center-demand-and-cooling-backlog-in-focus/ ; heygotrade, "Vertiv (VRT) Stock: Buy the Data Center Cooling Pure-Play?" — https://www.heygotrade.com/en/blog/vertiv-vrt-data-center-cooling-ai-2026/ ; Seeking Alpha, "Vertiv: The $15 Billion Backlog…" — https://seekingalpha.com/article/4890719-vertiv-holdings-the-15-billion-backlog-liquid-cooling-dominance-and-the-ai-infrastructure-trade-wall-street-is-still-underpricing
21. Investing.com, "Prysmian Q1 2026 slides: margin expansion accelerates on data center push" — https://www.investing.com/news/company-news/prysmian-q1-2026-slides-margin-expansion-accelerates-on-data-center-push-93CH-4648257 ; Insurance Journal, "Prysmian Eyes New Texas Copper Mill Amid Data Center Boom" — https://www.insurancejournal.com/news/southcentral/2026/03/19/862673.htm
22. Mordor Intelligence, "Data Center Wire And Cable Market" — https://www.mordorintelligence.com/industry-reports/data-center-wire-and-cable-market ; Bitget News, "Prysmian's 2027 Texas Facility: Capitalizing on Copper Shortages…" — https://www.bitget.com/news/detail/12560605277700
23. Macrotrends, "Oklo Market Cap 2022-2026" — https://www.macrotrends.net/stocks/charts/OKLO/oklo/market-cap ; Utility Dive, "Oklo reveals 75-MW reactor design, eyes late 2027 commercial deployment" — https://www.utilitydive.com/news/oklo-75-mw-reactor-design-smr-nuclear/743578/ ; Carbon Credits, "NuScale Power Stock Surges After U.S. Biggest SMR Nuclear Deal" — https://carboncredits.com/nuscale-power-stock-surges-after-u-s-biggest-smr-nuclear-deal/ ; Neutron Bytes, "NuScale and ENTRA1 Expect $25 Billion from US/Japan Trade Deal" — https://neutronbytes.com/2025/10/30/nuscale-and-entra1-get-25-billion-from-us-japan-trade-deal/
24. IndexBox, "Nuclear Energy Stocks: BWX Technologies and Rolls-Royce Lead SMR Push for AI Data Centers" — https://www.indexbox.io/blog/nuclear-energy-stocks-bwx-technologies-and-rolls-royce-lead-smr-push-for-ai-data-centers/ ; StockTitan, "Nuclear & Uranium Stocks 2026" — https://www.stocktitan.net/stocks/themes/nuclear-stocks
25. Foreign Policy Journal, "Nuclear Capital Flows Heat Up: Cameco (CCJ)… Centrus Energy (LEU)…" (15/jun/2026) — https://www.foreignpolicyjournal.com/2026/06/15/nuclear-capital-flows-heat-up-cameco-nyse-ccj-global-x-uranium-etf-nysearca-ura-and-centrus-energy-nyse-leu-lead-the-charge/ ; Motley Fool, "This Nuclear Stock Could Be a Big Winner as the U.S. Rushes to Secure Its Fuel Supply (LEU)" — https://www.fool.com/investing/2026/02/12/nuclear-stock-big-winner-as-us-fuel-supply-leu/ ; Yahoo/TradingView, "Cameco vs. Centrus Energy" — https://finance.yahoo.com/markets/stocks/articles/cameco-vs-centrus-energy-uranium-121800042.html
26. Manufacturing Dive, "Caterpillar to triple power generation capacity, raises 2030 targets" — https://www.manufacturingdive.com/news/caterpillar-triple-power-generation-capacity-raises-2030-targets-q1-2026-earnings/819078/ ; TIKR, "Caterpillar Power Chief Just Revealed What the Data Center Boom Really Means for CAT Stock" — https://www.tikr.com/blog/caterpillar-power-chief-just-revealed-what-the-data-center-boom-really-means-for-cat-stock ; MarketsandMarkets, "Data Center Generators Market (Cummins/Caterpillar)" — https://www.marketsandmarkets.com/ResearchInsight/data-center-generators-companies.asp
27. MarketsandMarkets, "North America BESS Market (Tesla/GE Vernova)" — https://www.marketsandmarkets.com/ResearchInsight/north-america-battery-energy-storage-system-companies.asp ; exoswan, "Top Energy Storage Stocks 2026" — https://exoswan.com/energy-storage-stocks/ ; Fortune, "Data centers are finding a surprising way to deploy batteries" — https://fortune.com/2026/04/24/data-centers-ai-batteries-natural-gas-power/
28. enkiAI, "Gigawatt PPAs: How AI Redefined Hyperscaler Energy in 2026" — https://enkiai.com/solar/gigawatt-ppas-how-ai-redefined-hyperscaler-energy-in-2026/ ; pv magazine USA, "AI datacenters rewrite the solar PPA playbook" (13/mar/2026) — https://pv-magazine-usa.com/2026/03/13/ai-datacenters-rewrite-the-solar-ppa-playbook/ ; Carbon Credits, "Meta and NextEra Partner for a Big Solar and Storage Energy Deal" — https://carboncredits.com/meta-and-nextera-partner-for-a-big-solar-and-storage-energy-deal/

---

*Relatório de pesquisa (benchmark). Não constitui recomendação de investimento. Dados de mercado e backlogs refletem reportes do 4T25/1T26 e anúncios até junho de 2026; valores de market cap de empresas pré-receita (ex.: OKLO) são altamente voláteis. Divergências entre fontes foram sinalizadas no texto.*
