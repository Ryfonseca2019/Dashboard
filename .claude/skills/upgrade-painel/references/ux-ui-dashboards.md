# Boas práticas de UX/UI para painéis

Síntese das referências mais usadas em design de dashboards, para complementar o *Storytelling com Dados*.
Cite a referência curta (entre colchetes) em cada achado.

## Fundamentos

- **[Few] Stephen Few, *Information Dashboard Design*.** Um painel é uma tela de informação que se entende
  "num relance". Erros clássicos: passar de uma tela, falta de contexto nos números, detalhe ou precisão em
  excesso, medidas mal escolhidas, visual inadequado, variedade de visuais sem motivo, cores e decorações
  desnecessárias, layout sem hierarquia e destaque do que não importa.
- **[Shneiderman] Mantra da busca visual:** visão geral primeiro, depois zoom e filtro, detalhes sob demanda.
  Em Power BI: página resumo → páginas por tema com segmentações → drill-through/tooltip para o detalhe.
- **[Pirâmide] Pirâmide invertida de leitura:** no topo os KPIs e a manchete, no meio tendências e comparações,
  embaixo as tabelas de detalhe.
- **[Z/F] Padrão de leitura:** o olhar começa no canto superior esquerdo. O que está lá é lido primeiro.
- **[5s] Regra dos 5 segundos:** em 5 segundos, o usuário deve saber se a situação está boa ou ruim.

## Heurísticas de Nielsen adaptadas a painéis [Nielsen]

1. **Visibilidade do estado:** mostre data/hora da última atualização e os filtros ativos.
2. **Correspondência com o mundo real:** nomes de negócio (não `Sum of CODCOLIGADA`), unidades e formatos locais.
3. **Controle e liberdade:** botão para limpar filtros; navegação de volta do drill-through.
4. **Consistência e padrões:** segmentações sempre no mesmo lugar, mesmas cores para as mesmas categorias,
   mesmo tamanho de página, mesma tipografia.
5. **Prevenção de erros:** padrões de filtro sensatos (ano atual), avisos quando o dado está incompleto.
6. **Reconhecer em vez de lembrar:** rótulos diretos, legendas próximas, títulos que dizem o filtro aplicado.
7. **Eficiência:** atalhos (bookmarks, navegador de páginas) para quem usa todo dia.
8. **Estética minimalista:** só o necessário (ver L3).
9. **Ajudar a entender problemas:** mensagens claras quando um visual fica vazio ("Sem turmas no período").
10. **Ajuda e documentação:** página "Sobre/Como ler", descrições nas medidas e tooltips explicativos.

## Layout e UI

- **Grade:** margens e espaçamentos constantes (múltiplos de 8 px; neste repositório, margem de 24 e espaço de
  16–24). Alinhe as bordas esquerda/direita e o topo de visuais da mesma linha.
- **Hierarquia tipográfica:** título da página 20–24 pt; títulos de visual 12–14 pt; rótulos ≥ 10 pt; no
  máximo 2 famílias de fonte (Segoe UI no padrão Power BI).
- **Densidade:** até 8–10 visuais de dados por página; até 3–4 segmentações visíveis (demais no painel de
  filtros ou num painel lateral recolhível com bookmark).
- **Cartões de KPI:** valor + comparação (meta, variação, período anterior) + indicação de bom/ruim.
- **Números:** formato explícito (milhar, %, casas decimais coerentes), abreviação (mil, mi) quando a
  precisão não importa.
- **Tema:** um tema JSON corporativo (cores, fontes, fundos, bordas desativadas) dá consistência sem repetir
  formatação visual a visual.

## Acessibilidade [WCAG 2.2 / Microsoft]

- Contraste de texto ≥ **4,5:1** (texto normal) e ≥ **3:1** (texto grande ≥ 18 pt ou 14 pt negrito, e elementos
  gráficos essenciais).
- Não use só a cor para codificar significado: acrescente rótulo, ícone ou forma. Evite vermelho × verde sozinhos.
- Preencha o **texto alternativo** dos visuais (lido por leitores de tela).
- Defina a **ordem de tabulação** (`tabOrder`) seguindo a ordem de leitura; não repita valores.
- Teste com o filtro de daltonismo e com zoom de 200%.

## Notação de negócio [IBCS]

Do padrão IBCS (Hichert): mesma notação para o mesmo conceito em todo o relatório. Realizado em cor sólida,
meta/plano em contorno ou cinza, variação positiva/negativa sempre com as mesmas cores, períodos no eixo
horizontal e categorias no vertical.

## Navegação e interação no Power BI

- Mais de 6–8 páginas: navegador de páginas ou botões, e páginas de detalhe ocultas e acessadas por drill-through.
- **Drill-through** para a ficha de uma entidade (turma, unidade, curso).
- **Páginas de dica de ferramenta (tooltip)** para contexto sem ocupar espaço.
- **Bookmarks** para alternar visões (gráfico ↔ tabela) em vez de duplicar páginas.
- **Interações entre visuais:** revise o filtro cruzado; desative onde ele confunde.
- **Layout para celular** nas páginas de resumo, se o público acessa pelo telefone.

## Desempenho percebido

Cada visual é uma ou mais consultas: menos visuais por página = página mais rápida. Prefira medidas explícitas a
agregações implícitas, evite tabelas com dezenas de colunas e muitos milhares de linhas na primeira página, e
evite relacionamentos bidirecionais sem necessidade.
