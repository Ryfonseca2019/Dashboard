# Storytelling com Dados aplicado a painéis Power BI

Referência: Cole Nussbaumer Knaflic, *Storytelling com Dados: um guia sobre visualização de dados para
profissionais de negócios* (Alta Books; original *Storytelling with Data*, Wiley, 2015). Abaixo estão as seis
lições do livro resumidas com nossas palavras e traduzidas em verificações concretas para PBIR. Cite a lição
(L1–L6) em cada achado do relatório de upgrade.

## L1 — Entenda o contexto

- **Exploratório × explicativo.** Exploratório é procurar algo nos dados. Explicativo é mostrar ao público o
  que importa. Um painel de gestão é explicativo; uma página de conferência/exportação é exploratória e pode
  continuar densa, mas não deve ser a primeira página.
- **Quem, o quê, como.** Quem é o público e que decisão ele toma; o que você quer que ele saiba ou faça; como
  os dados sustentam isso (dados demais = ruído).
- **Grande ideia.** Uma frase completa com o ponto de vista e o que está em jogo. Ex.: "Niterói está 18% abaixo
  da meta de H/A e o atraso vem de turmas sem horário cadastrado".
- **História de 3 minutos.** Se o público só tiver 3 minutos, o que precisa ouvir? Isso define a página inicial.
- **Storyboard antes do Desktop.** Esboce as páginas em papel/texto antes de criar visuais.

Verificações: existe página de resumo explicativa? A primeira página responde à pergunta principal do público?
Páginas operacionais estão separadas das gerenciais?

## L2 — Escolha um visual adequado

| Situação | Prefira | Evite |
|---|---|---|
| 1–2 números importantes | Texto grande/cartão **com comparação** (meta, período anterior) | Cartão isolado sem referência |
| Consulta de valores exatos | Tabela enxuta, poucas colunas, destaque leve | Tabela como única forma de análise |
| Muitos valores numa grade | Mapa de calor (tabela com formatação condicional) | — |
| Evolução no tempo | Linha (contínua) | Barras com dezenas de períodos, pizza |
| Comparar categorias | Barras horizontais **ordenadas**, eixo começando em zero | Pizza/rosca, 3D, eixo truncado em barras |
| Mudança entre dois pontos | Slopegraph (linha com 2 pontos por categoria) | Duas pizzas |
| Partes de um todo | Barras empilhadas 100% com poucas séries | Rosca com muitas fatias |
| Real × meta | Colunas/barras com linha ou marcador de meta, variação explícita | Medidor (gauge) |

- Rótulos longos → barras horizontais.
- Eixo secundário confunde: rotule as séries direto ou divida em dois gráficos.
- Barras empilhadas: só a primeira série tem base comum; use pouco.

## L3 — Elimine a desordem

Cada elemento cobra carga cognitiva. Pergunte de cada um: "se eu tirar, alguém sente falta?".

- **Gestalt:** proximidade (o que está junto parece relacionado), semelhança (mesma cor/forma = mesma coisa),
  cercamento (fundo/área agrupa), fechamento, continuidade e conexão (linhas ligam pontos).
- **Ordem visual:** alinhe a uma grade, mantenha espaçamento constante, use espaço em branco de propósito.
  Desalinhamentos de poucos pixels parecem descuido.
- **Contraste estratégico:** se tudo está destacado, nada está.
- **Remova:** bordas e sombras de visuais, linhas de grade fortes, marcadores desnecessários, legendas quando dá
  para rotular direto, casas decimais sem valor, rótulos redundantes com o eixo, títulos de eixo óbvios.
- Menos visuais por página (referência prática: até 8–10 visuais de dados). Também melhora o desempenho, porque
  cada visual é uma consulta.

## L4 — Foque a atenção do público

- **Atributos pré-atentivos:** cor, intensidade, tamanho, posição, negrito, cercamento. O olho os percebe antes
  de ler; use-os só no que importa.
- **Cor com parcimônia:** base em cinza e uma cor de destaque para a mensagem. Mantenha cores consistentes entre
  páginas (a mesma categoria tem sempre a mesma cor). Evite vermelho × verde como única diferença (daltonismo).
- **Posição:** o olhar começa no canto superior esquerdo e segue em Z/F. Coloque ali o KPI ou a manchete.
- **Tamanho:** o que é maior parece mais importante; a hierarquia de tamanho deve seguir a de importância.
- **Em Power BI:** formatação condicional para destacar só o que está fora da meta; cor de destaque nas barras
  relevantes e cinza nas demais; marcas de referência (linha de meta, média).

## L5 — Pense como um designer

- **Affordances:** destaque o importante, elimine distrações, crie hierarquia visual clara (manchete → KPIs →
  tendência → detalhe).
- **Acessibilidade:** não complique; use texto para explicar. Títulos de ação, subtítulos com a unidade e o
  período, anotações nos pontos que importam. Contraste e tamanho de fonte legíveis.
- **Estética:** alinhamento, espaço em branco e cores harmoniosas aumentam a confiança e a tolerância do público.
- **Aceitação:** mudanças grandes de layout precisam ser explicadas (antes × depois, por que é melhor) e, se
  possível, oferecidas como opção.

## L6 — Conte uma história

- **Estrutura:** início (contexto, situação), meio (tensão: o problema, o desvio, o risco), fim (a ação
  recomendada). Num painel: página resumo → páginas de diagnóstico → páginas de detalhe/ação.
- **Títulos de ação:** o título diz a conclusão, não o conteúdo. "H/A por unidade" → "Três unidades concentram
  70% do GAP de H/A". Títulos dinâmicos (medida DAX que gera texto) mantêm a frase verdadeira quando o filtro muda.
- **Lógica horizontal:** lendo só os títulos das páginas em sequência, a história deve fazer sentido.
  **Lógica vertical:** tudo numa página sustenta o título dela.
- **Repetição:** retome a grande ideia no início e no fim.

## Checklist rápido para o relatório de upgrade

1. A primeira página diz em 5 segundos como está a situação e o que fazer? (L1, L6)
2. Cada visual é o tipo mais simples que responde à pergunta? (L2)
3. Dá para remover algo sem perder informação? (L3)
4. Há uma única coisa destacada por visual, com cor de destaque sobre base neutra? (L4)
5. Títulos são frases de conclusão, com unidade e período? (L5, L6)
6. Os títulos das páginas, lidos em ordem, contam a história? (L6)
