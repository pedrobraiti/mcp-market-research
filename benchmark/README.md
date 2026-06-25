# Benchmark — Claude Code (deep research) vs. claude.ai (web)

Objetivo: medir, lado a lado, a qualidade de pesquisa que o **Claude Code** consegue gerar
(agentes + WebSearch/WebFetch) contra o produto **claude.ai (web)** com pesquisa nativa, para
decidir como Scout deve tratar a camada narrativa/qualitativa (a parte que NÃO é dado
estruturado). Decisão por evidência, não por suposição.

## Método
1. Três perguntas de pesquisa canônicas (variadas: empresa, tema/setor, macro) — ver
   `PROMPTS-FOR-CLAUDE-WEB.md`.
2. **Lado Claude Code:** um subagente por pergunta fez pesquisa web exaustiva e salvou o
   relatório em `claude-code/`. (Já gerado.)
3. **Lado claude.ai web:** o usuário cola cada prompt num chat novo do claude.ai, baixa o
   relatório em Markdown e salva em `claude-web/` com o MESMO nome de arquivo.
4. Comparação 1-a-1: profundidade, precisão factual, qualidade/atualidade das fontes,
   tratamento de incerteza, e utilidade para uma decisão de investimento.

## Arquivos
- `claude-code/01-nvda.md` — análise NVDA (17 buscas, ~45 fontes).
- `claude-code/02-infra-energia-ia.md` — cadeia de infra de energia p/ IA (21 buscas, ~70 URLs).
- `claude-code/03-macro-h2-2026.md` — macro 2º sem. 2026 (12 buscas, ~55 fontes).
- `claude-web/` — a preencher com os relatórios do claude.ai web (mesmos nomes).

## Aviso
Estes são **artefatos de avaliação**, não recomendação de investimento. Pesquisa sobre temas
recentes/prospectivos pode conter conteúdo especulativo ou desatualizado — avaliar como cada
lado lida com a incerteza faz parte do teste.
