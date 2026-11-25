# Catálogo de novas visões

Padrões que o `analisar_painel.py` procura no modelo. Use-os também na revisão qualitativa: se o script não
disparou um padrão, mas o contexto do usuário pede, proponha assim mesmo.

| Código | Visão | Quando sugerir | Estrutura (topo → base) | Princípio |
|---|---|---|---|---|
| NV01 | Resumo executivo | Nenhuma página com ≥ 2 KPIs no topo | Manchete · 3–4 KPIs com comparação · tendência · ranking | L1 história de 3 min, L6, pirâmide |
| NV02 | Realizado × meta | Há medida de meta e a medida base, mas nunca na mesma página | KPIs (realizado, meta, GAP, %) · barras realizado × meta por dimensão · linha no tempo | L1 contexto, L4 foco no desvio, IBCS |
| NV03 | Tendências | Medidas importantes nunca exibidas no tempo | Linhas por competência/mês, uma medida por gráfico | L2 linha para tempo |
| NV04 | Recortes não explorados | Colunas de dimensão sem uso em visuais | Barras ordenadas por dimensão + tabela de detalhe | L2 barras ordenadas |
| NV05 | Qualidade e pendências | Medidas de pendência/erro/validação | KPIs de pendência · tabela por unidade/responsável | L4 foco no que exige ação |
| NV06 | Ficha (drill-through) | Dimensão com ID e nenhuma página de drill-through | KPIs da entidade · tabela de atributos | Shneiderman: detalhe sob demanda |
| NV07 | Tema não explorado | Pasta de medidas (displayFolder) sem nenhuma medida no relatório | KPIs da pasta · barras por dimensão principal | L1 contexto |
| NV08 | Relação entre medidas | ≥ 2 medidas base com dimensão comum | Dispersão por dimensão (atípicos) | L2 dispersão |
| NV09 | Dica de ferramenta | Nenhuma página de tooltip | 2–3 cartões pequenos (página 320×240) | L3 menos desordem |

Outras visões para considerar caso a caso (não detectadas automaticamente):

- **Comparativo entre períodos** (slopegraph ano anterior × atual) quando há dois anos de dados.
- **Pareto** (80/20) quando poucas categorias concentram o volume.
- **Mapa de calor** (matriz com formatação condicional) para dimensão × tempo.
- **Página "Como ler este painel"**: definições das medidas, fonte, data de atualização, contatos.
- **Layout para celular** da página de resumo.

## Como transformar uma visão em página

1. O script grava `specs/NVxx.json` quando todos os visuais são suportados pelo gerador.
2. Antes de gerar, **reescreva os títulos** como títulos de ação (L6) e a manchete (textbox) com a grande ideia.
   Títulos que dependem do número atual: escreva um título neutro e descritivo (ex.: "H/A prevista × meta por
   unidade, ano selecionado") e proponha uma medida DAX de título dinâmico como passo seguinte.
3. Gere com `pbir-paginas-visuais/scripts/pbir_tool.py criar <projeto> specs/NVxx.json`.
4. Para NV06 e NV09, avise que o drill-through e a configuração de tooltip são feitos no Desktop.
