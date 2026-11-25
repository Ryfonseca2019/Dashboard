# Catálogo de novas visões

Padrões que o `analisar_painel.py` procura no modelo. Use-os também na revisão qualitativa: se o script não
disparou um padrão, mas o contexto do usuário pede, proponha assim mesmo.

| Código | Visão | Quando sugerir | Estrutura (topo → base) | Princípio |
|---|---|---|---|---|
| NV01 | Resumo executivo | Nenhuma página com ≥ 2 KPIs no topo | Manchete · 3–4 KPIs · tendência · ranking com as 3 maiores em destaque | L1 história de 3 min, L6, pirâmide |
| NV02 | Realizado × meta | Há medida de meta e a medida base, mas nunca na mesma página | KPI com título dinâmico (% da meta) · `real_meta` (laranja abaixo da meta) · linha no tempo | L1 contexto, L4 foco no desvio, IBCS |
| NV03 | Tendências | Medidas importantes nunca exibidas no tempo | Linhas por competência/mês, uma medida por gráfico | L2 linha para tempo |
| NV04 | Recortes não explorados | Colunas de dimensão sem uso em visuais | Barras ordenadas por dimensão + tabela de detalhe | L2 barras ordenadas |
| NV05 | Qualidade e pendências | Medidas de pendência/erro/validação e nenhuma página que as reúna | KPIs de pendência · Pareto por unidade · tabela | L4 foco no que exige ação |
| NV06 | Ficha (drill-through) | Dimensão com ID e nenhuma página de drill-through | Página drill-through configurada + botão Voltar · KPIs · tabela | Shneiderman: detalhe sob demanda |
| NV07 | Tema não explorado | Pasta de medidas (displayFolder) sem nenhuma medida no relatório | KPIs da pasta · barras por dimensão principal | L1 contexto |
| NV08 | Relação entre medidas | ≥ 2 medidas base e nenhuma dispersão | Dispersão por dimensão (atípicos) | L2 dispersão |
| NV09 | Dica de ferramenta | Nenhuma página de tooltip | Página de dica 320×240 configurada; ligar com `formatar {tooltip_pagina}` | L3 menos desordem |
| NV10 | Mapa de calor | Dimensão + tempo sem matriz equivalente | Matriz dimensão × período com gradiente | L2 mapa de calor, L4 intensidade |
| NV11 | Slopegraph | O perfil de dados mostra ≥ 2 anos | Linha por categoria entre os dois últimos anos | L2 mudança entre dois pontos |

Outras visões para considerar caso a caso (não detectadas automaticamente):

- **Pareto** de outras medidas quando a manchete do perfil mostra concentração (top 3 com mais de 60%).
- **Página "Como ler este painel"**: definições das medidas, fonte, data de atualização, contatos.
- **Layout para celular** da página de resumo.

## Como transformar uma visão em página

1. O script grava `specs/NVxx.json` quando todos os visuais são suportados pelo gerador.
2. Antes de gerar, **reescreva os títulos** como títulos de ação (L6) e a manchete (textbox) com a grande ideia.
   Títulos que dependem do número atual: use `"titulo_dinamico": {"medida", "meta", "texto"}` no visual (a medida
   DAX é criada) ou um título neutro e descritivo (ex.: "H/A prevista × meta por unidade, ano selecionado").
3. Gere com `pbir-paginas-visuais/scripts/pbir_tool.py criar <projeto> specs/NVxx.json`.
4. NV06 e NV09 já saem configuradas (drill-through com Voltar, página de dica). Para usar a dica num gráfico:
   grave `{"<id do visual>": {"tooltip_pagina": "<nome da página de dica>"}}` em `f.json` e rode
   `pbir_tool.py formatar <projeto> f.json`.
