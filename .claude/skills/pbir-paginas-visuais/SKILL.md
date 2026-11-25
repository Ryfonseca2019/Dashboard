---
name: pbir-paginas-visuais
description: Adiciona páginas e visuais (cartões, segmentações, barras, colunas, linhas, rosca, tabelas, matrizes e títulos) em relatórios Power BI no formato PBIP/PBIR deste repositório, usando os campos reais do modelo TMDL e o padrão visual dos painéis existentes, e valida o resultado antes da entrega. Use quando o pedido for criar uma página nova, incluir ou reposicionar visuais, montar uma visão/aba nova no painel ou fazer upgrade de layout de um .Report.
---

# Páginas e visuais em PBIR

Os painéis deste repositório são projetos PBIP: `<Nome>.Report/definition/pages/<id>/page.json`,
`.../visuals/<id>/visual.json` e o modelo em `<Nome>.SemanticModel/definition/tables/*.tmdl`.
As entregas são versionadas (`..._vNN.zip`, pastas `Entrega_*`) e abertas pelo usuário no Power BI Desktop
na rede corporativa. Daqui não dá para abrir o Desktop, então a qualidade depende da validação estática abaixo.

Ferramentas (rode com `python3 -I`; `<skill>` = `.claude/skills/pbir-paginas-visuais`):

| Comando | Para quê |
|---|---|
| `<skill>/scripts/pbir_tool.py campos <projeto> [--busca txt] [--tabela Nome]` | Lista tabelas, colunas e medidas reais do TMDL |
| `<skill>/scripts/pbir_tool.py criar <projeto> <spec.json> [--simular]` | Cria página nova ou adiciona visuais a uma existente, e já valida |
| `<skill>/scripts/pbir_tool.py ajustar <projeto> [--pagina P] [--titulos t.json] [--texto-alt] [--ordem-leitura] [--simular]` | Em visuais existentes: troca títulos (`{"<id visual>": "Título"}`), preenche texto alternativo com o título e renumera z/tabOrder na ordem de leitura |
| `<skill>/scripts/pbir_tool.py validar <projeto>` | Estrutura, IDs, `pageOrder`, limites, sobreposição e campos inexistentes |
| `<skill>/scripts/validar_schema.py <projeto> [id_pagina ...]` | Confere os JSON com os schemas oficiais da Microsoft (precisa de `jsonschema` e rede) |

`<projeto>` pode ser a pasta com o `.pbip`, a pasta `*.Report` ou o arquivo `.pbip`.

## Fluxo

1. **Base certa.** Descubra qual é a entrega mais recente do painel (maior `vNN`, último commit). Nunca altere
   uma versão já entregue: extraia o ZIP (ou copie a pasta) para uma pasta de trabalho nova. Se o pedido não deixar
   claro qual painel, pergunte.
2. **Campos.** Rode `campos` com `--busca` para achar as medidas/colunas certas. Use só o que existe no modelo.
   Se falta uma medida, crie-a no TMDL primeiro (siga a skill de DAX/modelagem, com `lineageTag` novo e
   `displayFolder` sem duplicar) e só depois o visual.
3. **Layout.** Leia 1–2 `page.json`/`visual.json` de páginas existentes do mesmo relatório e mantenha largura,
   altura, `displayOption` e cores. Monte o layout na grade abaixo. Para páginas com mais de 4 visuais, mostre ao
   usuário um esboço em texto (linhas e o que vai em cada uma) antes de gerar.
4. **Spec.** Escreva um `spec.json` (modelo em `exemplos/pagina_nova.json`), de preferência no scratchpad.
5. **Gerar.** `criar ... --simular` para conferir, depois `criar`. O script escolhe IDs únicos de 20 hex,
   reutiliza a versão de `$schema` mais usada no relatório, atualiza `pages.json` e roda `validar`.
6. **Validar.** `validar` precisa terminar com **0 erro(s)**. Avisos antigos (ex.: z repetido em páginas que já
   existiam) não bloqueiam, mas não introduza novos. Rode `validar_schema.py <projeto> <id_da_pagina> pages.json`.
7. **Entrega.** Siga o padrão das entregas anteriores: novo ZIP `vNN+1`, `LEIA_ME` dizendo o que mudou, em qual
   página, o que foi conferido e que a renderização real depende de abrir no Desktop. Não diga que "funciona"
   sem essa ressalva.

## Spec

```json
{
  "pagina": { "nome": "Nome visível", "largura": 1440, "altura": 1100, "depois_de": "<id página>", "ativa": false },
  "visuais": [
    { "tipo": "card", "titulo": "Turmas em execução",
      "campos": { "Values": "FatoProducao[Turmas em Execução]" },
      "posicao": { "x": 24, "y": 180, "largura": 330, "altura": 120 } }
  ]
}
```

- Página existente: `"pagina": { "existente": "<id da pasta ou displayName exato>" }` (z continua do maior atual).
- Opcionais da página nova: `ajuste` (`FitToPage` padrão, `FitToWidth` nas páginas largas do RM), `fundo` (cor ou `null`).
- Campos sempre `Tabela[Campo]`. O script decide sozinho se é `Column` ou `Measure` pelo TMDL; errar isso é a
  causa mais comum de visual quebrado ao abrir.
- `card`: `tamanho_valor` (padrão 27). `slicer`: `modo` (`Dropdown` padrão, ou `Basic`).
  `textbox`: `texto`, `tamanho_fonte` (padrão `24pt`).

| tipo (apelido) | Papéis aceitos |
|---|---|
| `card` (cartao) | `Values` (uma medida) |
| `slicer` (segmentacao) | `Values` (uma coluna) |
| `tableEx` (tabela) | `Values` (lista) |
| `pivotTable` (matriz) | `Rows`, `Columns`, `Values` |
| `clusteredBarChart` (barras), `clusteredColumnChart` (colunas), `lineChart` (linha) | `Category`, `Y`, `Series`, `Tooltips` |
| `donutChart` (rosca) | `Category`, `Y`, `Tooltips` |
| `textbox` (texto, titulo) | sem campos |

## Padrão visual dos painéis

- Página 1440 de largura (1000–1100 de altura), fundo `#F3F6FA`; visuais com fundo `#FFFFFF`, sem borda/sombra.
- Títulos `#163B65` 12pt; valor de cartão `#0072CE`; título da página em textbox 24pt `#163B65`.
- Grade: margem 24, espaço de 16–24 entre visuais.
  - Título: `x 24, y 14, 1392 × 55`
  - Segmentações: `y 84`, `268 × 80`, passo de 284 em x
  - Cartões (até 4): `y 180`, `330 × 120`, x = 24, 378, 732, 1086
  - Dois gráficos: `688 × 300–340`, x = 24 e 728
  - Tabela/visual largo: `x 24`, largura 1392
- Páginas de conferência/exportação do RM (`Entrega_RM_*`) usam outro padrão: `FitToWidth`, 4200 × 1400,
  tabelas `tableEx` de largura total. Mantenha esse padrão nelas.
- Para escolher o visual, a hierarquia, as cores e o texto, siga as referências da skill `upgrade-painel`:
  `.claude/skills/upgrade-painel/references/storytelling-com-dados.md` (lições L1–L6 do livro *Storytelling com
  Dados*) e `.../ux-ui-dashboards.md`. Em resumo: manchete com a conclusão, KPIs com comparação no topo, um
  visual por pergunta, barras ordenadas para categorias e linha para tempo, base neutra com uma cor de destaque,
  títulos de ação. Para um upgrade completo de painel (análise + sugestões), use a skill `upgrade-painel`.

## O que o script não faz (edite o JSON à mão, copiando de um visual existente)

Filtros de visual/página (`filterConfig`), formatação condicional, bookmarks, botões, imagens, drill-through,
ordenação personalizada e visuais personalizados. Ao editar à mão:
- `name` do `page.json`/`visual.json` igual ao nome da pasta; ID novo e único no relatório inteiro.
- Toda página nova entra em `pageOrder`; `activePageName` precisa existir.
- `queryRef` = `Tabela.Campo`, `nativeQueryRef` = `Campo`, e `Column` vs `Measure` correto.
- Literais seguem o formato PBIR: texto `'...'` (aspas simples dobradas dentro), número `12D`, booleano `true`.
- UTF-8 sem BOM, acentos preservados (`ensure_ascii=False`). Não mexa em `.platform` (`logicalId`) nem em
  `definition.pbir`.
- Depois rode `validar` e `validar_schema.py` do mesmo jeito.
