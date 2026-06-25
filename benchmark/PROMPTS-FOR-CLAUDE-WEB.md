# Prompts para o claude.ai (web)

Cole CADA prompt abaixo num **chat novo** do claude.ai (use o modo de pesquisa/Research se
disponível). Ao terminar, **baixe o relatório em Markdown** e salve em
`benchmark/claude-web/` com o nome indicado. Depois me avise que eu comparo com o lado
Claude Code.

> Os prompts são quase idênticos aos dados aos meus subagentes — a única diferença é o
> mecanismo (o claude.ai já tem a pesquisa integrada; eu tive que instruir o agente a usar as
> tools). O conteúdo da pergunta é o mesmo, para a comparação ser justa.

---

## 1 → salvar como `claude-web/01-nvda.md`

```
Faça uma análise de investimento aprofundada da NVIDIA (NVDA), com data-base de junho de 2026:
(a) posição competitiva atual e ameaças (concorrência de AMD, custom silicon dos hyperscalers,
restrições à China); (b) principais riscos para os próximos 12 meses; (c) situação de valuation
frente ao próprio histórico e aos pares; (d) bull case e bear case bem articulados. Quero
profundidade real, não generalidades. Produza um relatório final em Markdown que eu possa
baixar, com todas as fontes citadas (veículo, título, data e link).
```

## 2 → salvar como `claude-web/02-infra-energia-ia.md`

```
Mapeie a tese de investimento de "infraestrutura de energia para data centers de IA", com
data-base de junho de 2026: a cadeia de valor completa (geração de energia, transmissão/grid,
equipamentos elétricos, refrigeração/cooling, nuclear e SMRs, gás natural) e os principais
players LISTADOS nos EUA em cada elo da cadeia — com o porquê de cada um pertencer ali e como
se diferenciam. Quero a cadeia toda, não só os nomes óbvios. Produza um relatório final em
Markdown que eu possa baixar, com todas as fontes citadas (veículo, título, data e link).
```

## 3 → salvar como `claude-web/03-macro-h2-2026.md`

```
Faça um panorama macro para ações americanas no 2º semestre de 2026: trajetória esperada da
taxa de juros do Fed, inflação (CPI/PCE), mercado de trabalho, crescimento (PIB) e as
implicações setoriais (quais setores se beneficiam e quais sofrem em cada cenário). Quero
números atuais e datados e o que o mercado está precificando. Produza um relatório final em
Markdown que eu possa baixar, com todas as fontes citadas (veículo, título, data e link).
```
