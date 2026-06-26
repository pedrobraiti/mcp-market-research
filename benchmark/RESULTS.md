# Resultado do benchmark — Claude Code (deep research) vs. claude.ai (web)

Avaliação cega por 3 juízes (um por tema), cada um lendo as duas versões e pontuando
profundidade, precisão factual, fontes, usabilidade e tratamento de incerteza.

## Placar

| Tema | Claude Code (A) | claude.ai web (B) | Margem |
|---|:---:|:---:|---|
| NVDA | 21/25 | 25/25 | B vence (clara, não esmagadora) |
| Macro H2 2026 | 22/25 | 23/25 | empate técnico |
| Infra de energia p/ IA | 20/25 (4,0/5) | 24/25 (4,8/5) | B vence (clara) |
| **Total** | **63/75 (84%)** | **72/75 (96%)** | **B vence por margem modesta** |

**Leitura:** a claude.ai web venceu os 3, mas por margens modestas. O Claude Code entregou
~**85–90% da qualidade**, e **nunca perdeu nos fatos centrais**.

## Achado central: convergência factual (não é alucinação)

Nos 3 temas, os dois lados **convergiram nos mesmos fatos reais**, com precisão de dígito:
- **NVDA**: receita Q1 FY27 US$ 81,6 bi, DC US$ 75,2 bi, EPS não-GAAP US$ 1,87, FCF ~US$ 49 bi, guidance Q2 US$ 91 bi, China zerada, backlog ~US$ 500 bi, P/L fwd ~20–23x.
- **Macro**: chair do Fed = Kevin Warsh (posse mai/2026), FOMC manteve 3,50–3,75% (12-0), dot plot 3,4%→3,8%, CPI mai 4,2%, payrolls +172k, S&P ~7.365, choque de energia Irã/Ormuz.
- **Infra**: mesma espinha (CEG/VST/TLN, GEV, ETN/VRT/POWL, OKLO/SMR/BWXT, CCJ/LEU…), fechamento da Calpine jan/2026, Talen-AWS, etc.

Como a data de corte do modelo é jan/2026 e a base é jun/2026, essa convergência prova que
**a pesquisa do Claude Code captou os mesmos eventos reais que a claude web** — não inventou.

## Onde cada lado ganha (o padrão importa mais que o placar)

**claude.ai web ganha consistentemente em:**
1. **Sourcing primário** — puxou dezenas de **8-Ks/10-Ks da SEC**; os agentes do Claude Code levaram **403 da SEC e de vários primários** e caíram em agregadores/trade-press.
2. **Tratamento de incerteza** — seções de *caveats* dedicadas (ex.: "backlog da BWXT é naval, não data center"; reconciliação das cifras de China da NVDA).
3. **Cenários/estrutura quantitativa** — tabelas de price targets, cenários bear/base/bull explícitos, market internals (VIX, spreads, curva).
4. **Atualidade fina** — ex.: OpenAI a US$ 30 bi (não US$ 100 bi).

**Claude Code ganha em:**
1. **Usabilidade/escaneabilidade** — sumários executivos em tabela, diagramas de cadeia, matriz "quem ganha o quê".
2. **Síntese narrativa** — ex.: o bear case contábil da NVDA (Burry/subdepreciação/financiamento circular) com mais densidade.
3. **Concisão e alguns nichos** (LTBR/CARR/FSLR; cabos/cobre).

## Conclusão para a arquitetura do Scout

O gap é **modesto e majoritariamente fechável do nosso lado** — e cada parte cai num lado
diferente da fronteira sentidos×cérebro:

- **Gap de sourcing primário = problema de CAPTURA (sentido).** A web venceu em boa parte
  porque **conseguiu buscar primárias que nossos agentes não conseguiram (403/anti-bot)**.
  Isso valida diretamente a ideia do usuário: uma tool **`extract(url)`** no Scout (fetch com
  headers corretos → markdown limpo), somada ao **adapter SEC já existente**, fecha boa parte
  desse gap.
- **Gap de caveats/cenários = problema de PROMPT/skill (cérebro).** Não é falta de dado; é
  como o relatório é estruturado. Resolve-se com uma boa **skill de deep research** (cérebro),
  não com tool nova.
- **Atualidade** ficou ~empatada; não justifica depender de copiar/colar pra claude web.

**Decisão:** manter a pesquisa **no Claude Code** (cérebro: skill/subagentes), porque já está
essencialmente no mesmo nível. O Scout entra só com o **sentido `extract`** para fechar o gap
de captura de primárias. O "mandar prompt pra claude.ai web" vira **escape hatch opcional**
(casos de fronteira), não mecanismo central. Ver ADR de 2026-06-25 em `.claude/decisions.md`.
