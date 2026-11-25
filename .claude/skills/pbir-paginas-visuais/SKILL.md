---
name: pbir-paginas-visuais
description: Cria e edita páginas e visuais em relatórios Power BI PBIP/PBIR deste repositório — cartões, segmentações, barras, colunas, linhas, rosca, tabelas, matrizes, mapa de calor, dispersão, realizado × meta, Pareto, slopegraph, botões e navegador; destaque com cor (Storytelling com Dados), títulos dinâmicos, linha de meta, tema corporativo, drill-through, dica de ferramenta, alinhamento, troca de tipo de visual, reordenação/renomeação de páginas e medidas DAX no TMDL — e valida tudo antes da entrega. Use para criar/alterar páginas ou visuais de um .Report ou aplicar as melhorias escolhidas num upgrade de painel.
---

# Páginas e visuais em PBIR

Os painéis deste repositório são projetos PBIP: `<Nome>.Report/definition/pages/<id>/page.json`,
`.../visuals/<id>/visual.json` e o modelo em `<Nome>.SemanticModel/definition/tables/*.tmdl`.
As entregas são versionadas (`..._vNN.zip`, pastas `Entrega_*`) e abertas no Power BI Desktop na rede
corporativa. Daqui não dá para abrir o Desktop: a qualidade depende da validação estática e do schema oficial.

Rode com `python3 -I`; `<s>` = `.claude/skills/pbir-paginas-visuais/scripts`. `<projeto>` = pasta com o `.pbip`,
pasta `*.Report` ou o `.pbip`. Todo comando que altera aceita `--simular` e termina validando.

| Comando | Para quê |
|---|---|
| `<s>/pbir_tool.py campos <projeto> [--busca txt] [--tabela T]` | Tabelas, colunas e medidas reais |
| `<s>/pbir_tool.py criar <projeto> <spec.json>` | Página nova (normal, drill-through, dica) ou visuais numa página existente; cria medidas do spec |
| `<s>/pbir_tool.py formatar <projeto> <f.json>` | Opções em visuais existentes: `{"<id>": {opções}}` (ver Opções) |
| `<s>/pbir_tool.py trocar-tipo <projeto> <id> <tipo>` | Pizza/rosca → barras, gauge → cartão, linha ↔ barras, tabela |
| `<s>/pbir_tool.py ajustar <projeto> [--titulos t.json] [--texto-alt] [--ordem-leitura]` | Títulos (`{"<id>": "Título"}`), texto alternativo, z/tabOrder na ordem de leitura |
| `<s>/pbir_tool.py alinhar <projeto> [--pagina P] [--tolerancia 8]` | Encaixa bordas quase alinhadas (desfaz o que causaria sobreposição) |
| `<s>/pbir_tool.py layout <projeto> <l.json>` | Reposiciona: `{"<id>": {"x":..,"y":..,"largura":..,"altura":..}}` |
| `<s>/pbir_tool.py paginas <projeto> [--ordem a,b] [--ativa P] [--renomear id=Nome] [--ocultar P] [--mostrar P]` | Ordem, página inicial, nomes e visibilidade |
| `<s>/pbir_tool.py tema <projeto> [--nome N] [--destaque #hex] [--titulo #hex] [--fundo #hex] [--arquivo t.json]` | Tema corporativo (base neutra + destaque + status laranja, sem bordas/sombras) registrado no relatório |
| `<s>/pbir_tool.py navegacao <projeto> --posicao x,y,l,a [--paginas a,b]` | Navegador de páginas onde couber (pula páginas sem espaço) |
| `<s>/pbir_tool.py medida <projeto> --tabela T --nome N --expressao DAX\|@arq.dax [--formato F] [--pasta P] [--descricao D]` | Medida nova no TMDL |
| `<s>/pbir_tool.py validar <projeto>` | Estrutura, IDs, `pageOrder`, campos, drill-through, links de página, tema |
| `<s>/validar_schema.py <projeto> [id_pagina ...]` | Schemas oficiais da Microsoft (precisa de `jsonschema` e rede) |

## Fluxo

1. **Base certa:** trabalhe numa cópia da última entrega (nunca altere uma versão entregue).
2. **Campos:** `campos --busca`; use só o que existe. Medidas novas: `medida` ou `"medidas"` no spec.
3. **Layout:** siga a grade abaixo e o padrão das páginas existentes. Para mais de 4 visuais, mostre um esboço
   antes de gerar.
4. **Gerar/alterar:** `--simular` primeiro, depois para valer.
5. **Validar:** `validar` com 0 erro e `validar_schema.py` sem falhas. Leia as linhas `NOTA` (itens a conferir
   no Desktop) e repasse ao usuário.
6. **Entregar:** use `upgrade-painel/scripts/empacotar.py` (ZIP `vNN+1` + LEIA_ME com changelog).

## Spec de `criar`

```json
{
  "medidas": [{"tabela": "FatoProducao", "nome": "…", "expressao": "…", "formato": "0%", "pasta": "…"}],
  "pagina": {"nome": "Nome visível", "largura": 1440, "altura": 1100, "depois_de": "<id>", "ativa": false},
  "visuais": [
    {"tipo": "card", "titulo": "Turmas em execução", "campos": {"Values": "FatoProducao[Turmas em Execução]"},
     "posicao": {"x": 24, "y": 180, "largura": 330, "altura": 120}}
  ]
}
```

- Página existente: `"pagina": {"existente": "<id ou displayName>"}`.
- Página de **drill-through**: `"tipo": "drillthrough", "campo_drill": "DimTurma[TurmaID]"` (fica oculta e
  ganha botão Voltar; `"sem_voltar": true` desliga). **Dica de ferramenta**: `"tipo": "tooltip"` (320 × 240).
  Página oculta: `"oculta": true`. Opcionais: `ajuste`, `fundo`.
- Campos sempre `Tabela[Campo]`; o script decide `Column` × `Measure` pelo TMDL.

| tipo (apelido) | Papéis | Observação |
|---|---|---|
| `card` (cartao) | `Values` | `tamanho_valor` |
| `slicer` (segmentacao) | `Values` | `modo`: `Dropdown` ou `Basic` |
| `tableEx` (tabela) / `pivotTable` (matriz) | `Values` / `Rows`, `Columns`, `Values` | |
| `clusteredBarChart` (barras), `clusteredColumnChart` (colunas), `lineChart` (linha) | `Category`, `Y`, `Series`, `Tooltips` | barras/colunas saem ordenadas (desc; tempo asc) |
| `donutChart` (rosca) | `Category`, `Y` | evite (L2) |
| `scatterChart` (dispersao) | `Category`, `X`, `Y`, `Size`, `Series` | |
| `lineClusteredColumnComboChart` (combo) | `Category`, `ColumnY`, `Y` | |
| `real_meta` | `Category`, `Y`, `Meta` | colunas + marcador de meta no mesmo eixo, laranja abaixo da meta |
| `pareto` | `Category`, `Y` | cria a medida "% acumulado" e o combo ordenado |
| `slope` | `Category` (tempo), `Series`, `Y` + `"valores": [2025, 2026]` | linha filtrada em dois períodos |
| `mapa_calor` | `Rows`, `Columns`, `Values` | matriz com gradiente |
| `botao` | — | `acao`: `pagina`/`drillthrough` (+`destino`), `voltar`, `limpar_filtros`, `url`; `texto` |
| `navegador` | — | navegador de páginas |
| `textbox` (texto, titulo) | — | `texto`, `tamanho_fonte` |

## Opções (em `criar` e `formatar`)

| Opção | Efeito (princípio) |
|---|---|
| `"destaque": {"top": 3}` / `{"abaixo_de": "T[Meta]"}` / `{"acima_de": …}` / `{"categoria": "Niterói"}` / `{"medida_cor": "T[Cor]"}` | Base cinza + cor de destaque por medida DAX gerada (L4) |
| `"titulo_dinamico": {"medida": "T[M]", "meta": "T[Meta]", "texto": "H/A prevista", "formato": "#,0"}` | Título que se mantém verdadeiro com filtros (L6); cria a medida |
| `"titulo_medida": "T[Título]"` | Título ligado a medida existente |
| `"subtitulo": "…"` | Unidade, período ou legenda em texto (L5) |
| `"linha_meta": "T[Meta]"` ou número, `"rotulo_meta"` | Linha de referência no eixo de valores |
| `"ordenar": "desc"/"asc"/"asc_categoria"/"nenhuma"` | Barras ordenadas (L2) |
| `"legenda": false`, `"grade": false`, `"rotulos": true` | Menos desordem, rótulo direto (L3) |
| `"gradiente": true` | Mapa de calor em matrizes |
| `"tooltip_pagina": "<nome ou id>"` | Liga uma página de dica ao visual |
| `"texto_alt": "…"` | Texto alternativo (o padrão é o título) |
| `"modo": "Basic"` (formatar) | Segmentação em botões |
| `"titulo": "…"` (formatar) | Troca o título |

## Padrão visual dos painéis

- Página 1440 de largura (1000–1100 de altura), fundo `#F3F6FA`; visuais brancos, sem borda/sombra.
- Títulos `#163B65` 12 pt; valor de cartão `#0072CE`; manchete da página em textbox 24 pt.
- Destaque `#0072CE`, neutro `#BFC5CC`, alerta `#D9822B` (sem vermelho × verde, por daltonismo).
- Grade: margem 24, espaço 24. Título `x 24, y 14, 1392 × 55`; segmentações `y 84, 268 × 80`; cartões
  `330 × 120` em x = 24/378/732/1086; dois gráficos `688 × 300–340` em x = 24/728; largo `x 24, 1392`.
- Páginas de conferência do RM (`Entrega_RM_*`): `FitToWidth`, 4200 × 1400, tabelas largas; mantenha.
- Escolha de visual, cor e texto: siga `.claude/skills/upgrade-painel/references/storytelling-com-dados.md` e
  `ux-ui-dashboards.md`. Para o upgrade completo (análise + sugestões), use a skill `upgrade-painel`.

## Conferir no Desktop (o script avisa com `NOTA`)

- Medidas DAX geradas (cor, título, Pareto): sintaxe seguida do padrão do modelo, mas não executadas aqui.
- Linha de meta (`y1AxisReferenceLine`) e eixo único do realizado × meta (`secShow`).
- Botões e navegador: aparência; ação `limpar_filtros` requer Desktop recente.

## Ainda manual

Bookmarks (estado capturado é complexo e frágil para gerar), filtros Top N de visual, formatação condicional
por regras de faixa em tabelas e visuais personalizados. Ao editar JSON à mão: `name` igual à pasta, ID único,
página em `pageOrder`, `queryRef` = `Tabela.Campo`, literais PBIR (`'texto'`, `12D`, `true`), UTF-8 sem BOM;
não mexa em `.platform` nem `definition.pbir`; valide depois.
