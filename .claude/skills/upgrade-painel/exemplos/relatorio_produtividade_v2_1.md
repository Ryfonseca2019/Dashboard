# Análise de upgrade — Produtividade Planejamento de Turmas

Formato: **PBIP (PBIR)** · 7 páginas · 95 visuais · modelo: 13 tabelas, 38 medidas, 11 relacionamentos

Referências: *Storytelling com Dados* (lições L1–L6), Few, Nielsen, Shneiderman, WCAG, IBCS. Índices são heurísticos (100 = nenhum achado na categoria) e servem para priorizar, não para dar nota ao trabalho.

## Índices por dimensão

| Dimensão | Índice | Achados |
|---|---|---|
| Contexto e narrativa | 100 | 0 |
| Escolha do visual | 75 | 3 |
| Desordem e layout | 63 | 4 |
| Foco e cor | 97 | 1 |
| Acessibilidade | 91 | 2 |
| Navegação | 100 | 0 |
| Modelo e desempenho | 84 | 4 |

## Páginas

| # | Página | Tamanho | Visuais de dados | Segmentações | Uso |
|---|---|---|---|---|---|
| 1 | Visão Gerencial | 1440×1000 | 13 | 5 | gerencial |
| 2 | Detalhamento e Validação | 1440×1000 | 2 | 4 | operacional |
| 3 | Mobilização e oferta | 1440×1100 | 7 | 5 | gerencial |
| 4 | Oferta e capacidade | 1440×1100 | 7 | 5 | gerencial |
| 5 | Prontidão e pendências | 1440×1100 | 7 | 5 | gerencial |
| 6 | Evasão e memória de cálculo | 1440×1100 | 7 | 5 | gerencial |
| 7 | Cadastro e classificação contábil | 1440×1100 | 6 | 5 | gerencial |

## Melhorias sugeridas

Ordenadas por severidade. **Auto** = pode ser aplicada pelas skills sem edição manual no Desktop.

### M01 🔴 Visuais demais na página — Visão Gerencial
- **Por quê:** 'Visão Gerencial' tem 13 visuais de dados.
- **O que fazer:** Manter até 8–10: priorizar os que sustentam a manchete, mover o restante para uma página de detalhe, tooltip ou bookmark. Também reduz o tempo de carga.
- **Princípio:** L3 Carga cognitiva · [Few] · **Esforço:** médio · **Auto:** não · `D01`

### M02 🟠 Segmentações demais — Visão Gerencial, Mobilização e oferta, Oferta e capacidade, Prontidão e pendências, Evasão e memória de cálculo, Cadastro e classificação contábil
- **Por quê:** 6 ocorrências. 'Visão Gerencial' tem 5 segmentações; 'Mobilização e oferta' tem 5 segmentações; 'Oferta e capacidade' tem 5 segmentações; 'Prontidão e pendências' tem 5 segmentações; e mais 2
- **O que fazer:** Deixar 2–4 visíveis (período, unidade) e levar as demais ao painel de filtros ou a um painel lateral recolhível (bookmark). Sincronizar segmentações entre páginas.
- **Princípio:** L3 · [Nielsen 8] · **Esforço:** médio · **Auto:** não · `D02`

### M03 🟠 Tabela larga — Evasão e memória de cálculo, Cadastro e classificação contábil
- **Por quê:** 3 ocorrências. 'Memória por turma e competência — valores mensais sem agregação' em 'Evasão e memória de cálculo' tem 12 colunas; 'Classificação por turma' em 'Cadastro e classificação contábil' tem 11 colunas; 'Cadastro, responsáveis e rastreabilidade' em 'Cadastro e classificação contábil' tem 11 colunas
- **O que fazer:** Manter as colunas essenciais, aplicar destaque condicional só ao que exige ação e levar o restante para drill-through/tooltip.
- **Princípio:** L2 Tabelas para consulta · L3 · **Esforço:** médio · **Auto:** não · `G05`

### M04 🟠 Cartão sem comparação (há meta/variação no modelo) — Mobilização e oferta, Cadastro e classificação contábil
- **Por quê:** 2 ocorrências. 'H/A prevista parcial' mostra H/A Prevista no Painel sem referência. Medidas candidatas: Meta H/A, H/A Atingimento, H/A GAP; 'H/A prevista parcial' mostra H/A Prevista no Painel sem referência. Medidas candidatas: Meta H/A, H/A Atingimento, H/A GAP
- **O que fazer:** Mostrar meta, variação ou período anterior junto do valor (cartão novo com valor de referência, ou subtítulo dinâmico).
- **Princípio:** L1 Contexto · L2 Número com comparação · [Few] · **Esforço:** baixo · **Auto:** sim · `G09`

### M05 🟠 Sem tabela de datas marcada
- **Por quê:** Há colunas de tempo (Atualizacao[AtualizadoEmUTC], DimAno[Ano], DimCompetencia[Ano], DimCompetencia[AnoMes]) mas nenhuma tabela marcada como tabela de datas.
- **O que fazer:** Criar/marcar uma tabela calendário contínua e relacioná-la aos fatos.
- **Princípio:** Inteligência de tempo · **Esforço:** médio · **Auto:** não · `M04`

### M06 🟡 Visuais sem texto alternativo
- **Por quê:** 83 visual(is) de dados sem texto alternativo.
- **O que fazer:** Preencher o texto alternativo (Geral › Texto alternativo) com o que o visual mostra e a conclusão.
- **Princípio:** [WCAG] · [Microsoft] · **Esforço:** baixo · **Auto:** sim · `A03`

### M07 🟡 Ordem de camada/tabulação repetida — Mobilização e oferta, Oferta e capacidade, Prontidão e pendências, Evasão e memória de cálculo, Cadastro e classificação contábil
- **Por quê:** 5 ocorrências. Em 'Mobilização e oferta', 14 visuais compartilham o mesmo z/tabOrder; Em 'Oferta e capacidade', 14 visuais compartilham o mesmo z/tabOrder; Em 'Prontidão e pendências', 14 visuais compartilham o mesmo z/tabOrder; Em 'Evasão e memória de cálculo', 14 visuais compartilham o mesmo z/tabOrder; e mais 1
- **O que fazer:** Numerar z e tabOrder seguindo a leitura (esquerda→direita, cima→baixo).
- **Princípio:** [Microsoft] Ordem de tabulação · **Esforço:** baixo · **Auto:** sim · `A04`

### M08 🟡 Relatório sem tema corporativo
- **Por quê:** Só o tema base 'Fluent2-CY26SU08' está aplicado; cores e bordas são formatadas visual a visual.
- **O que fazer:** Criar um tema JSON (paleta: base cinza + cor de destaque + cores de status, Segoe UI, bordas e sombras desligadas) e aplicá-lo ao relatório.
- **Princípio:** L4 Cor consistente · [Nielsen 4] · **Esforço:** médio · **Auto:** não · `C02`

### M09 🟡 Pequenos desalinhamentos — Mobilização e oferta, Oferta e capacidade, Prontidão e pendências, Evasão e memória de cálculo
- **Por quê:** 4 ocorrências. 3 bordas quase alinhadas (diferença de 1–8 px) em 'Mobilização e oferta'; 3 bordas quase alinhadas (diferença de 1–8 px) em 'Oferta e capacidade'; 3 bordas quase alinhadas (diferença de 1–8 px) em 'Prontidão e pendências'; 3 bordas quase alinhadas (diferença de 1–8 px) em 'Evasão e memória de cálculo'
- **O que fazer:** Alinhar à grade (margem 24, espaçamento 16–24).
- **Princípio:** L3 Ordem visual · Gestalt · **Esforço:** baixo · **Auto:** sim · `D03`

### M10 🟡 Tamanhos de página diferentes
- **Por quê:** 1440×1100 (5 pág.), 1440×1000 (2 pág.)
- **O que fazer:** Padronizar o tamanho das páginas gerenciais (as de conferência podem manter o próprio).
- **Princípio:** [Nielsen 4] Consistência · **Esforço:** baixo · **Auto:** não · `D08`

### M11 🟡 Cartão sem comparação — Visão Gerencial, Mobilização e oferta, Oferta e capacidade, Evasão e memória de cálculo, Cadastro e classificação contábil
- **Por quê:** 14 ocorrências. 'Horas descontadas pelo calendário' mostra Horas Descontadas Calendário sem referência; 'Turmas em execução' mostra Turmas em Execução sem referência; 'Matrículas previstas' mostra Matrículas Previstas sem referência; 'Matrículas previstas' mostra Matrículas Previstas sem referência; e mais 10
- **O que fazer:** Mostrar meta, variação ou período anterior junto do valor (cartão novo com valor de referência, ou subtítulo dinâmico).
- **Princípio:** L1 Contexto · L2 Número com comparação · [Few] · **Esforço:** baixo · **Auto:** não · `G09`

### M12 🟡 Agregação implícita — Visão Gerencial
- **Por quê:** 'Última atualização' agrega Column1 direto da coluna.
- **O que fazer:** Criar medidas explícitas (formato, nome de negócio, reuso).
- **Princípio:** Boas práticas DAX · **Esforço:** baixo · **Auto:** não · `G10`

### M13 🟡 Medidas sem descrição
- **Por quê:** 38 de 38 medidas.
- **O que fazer:** Escrever descrições (aparecem ao passar o mouse e ajudam quem mantém o painel).
- **Princípio:** [Nielsen 10] Ajuda · **Esforço:** médio · **Auto:** não · `M03`

### M14 🟡 Medidas não usadas
- **Por quê:** 9 medida(s) sem uso em visuais nem em outras medidas: Atualização dos Dados UTC, H/A Acumulada no Ano, Turmas Negócio, Turmas Gratuidade, Título Produção H/A, Alerta de Cálculo, Turmas com planejamento ausente no período, Meta H/A no novo recorte….
- **O que fazer:** Avaliar se viram nova visão (ver sugestões) ou se podem ser removidas/ocultadas.
- **Princípio:** Oportunidade / limpeza · **Esforço:** baixo · **Auto:** não · `M05`

## Novas visões sugeridas

### NV03 🟠 Tendências no tempo
- **Pergunta que responde:** As principais medidas estão melhorando ou piorando?
- **Por quê:** Turmas no período, Matrículas Previstas, Vagas Previstas não aparecem ao longo de AnoMes.
- **Princípio:** L2 Linha para tempo · [Shneiderman] · **Auto:** sim · spec: `specs/NV03.json`
- **Visuais:**
  - lineChart — Evolução de Turmas no período (Category: DimCompetencia[AnoMes]; Y: FatoProducao[Turmas no período])
  - lineChart — Evolução de Matrículas Previstas (Category: DimCompetencia[AnoMes]; Y: FatoProducao[Matrículas Previstas])
  - lineChart — Evolução de Vagas Previstas (Category: DimCompetencia[AnoMes]; Y: FatoProducao[Vagas Previstas])

### NV04 🟠 Recortes ainda não explorados
- **Pergunta que responde:** Há padrões por Campo, ColunaModelo, CampoFonte?
- **Por quê:** Colunas de dimensão do modelo que não aparecem em nenhum visual.
- **Princípio:** L1 Contexto · L2 Barras ordenadas · **Auto:** sim · spec: `specs/NV04.json`
- **Visuais:**
  - clusteredBarChart — Turmas no período por Campo (Category: Campos_Adicionais_Diagnostico[Campo]; Y: FatoProducao[Turmas no período])
  - clusteredBarChart — Turmas no período por ColunaModelo (Category: Campos_Adicionais_Diagnostico[ColunaModelo]; Y: FatoProducao[Turmas no período])
  - clusteredBarChart — Turmas no período por CampoFonte (Category: Campos_Adicionais_Diagnostico[CampoFonte]; Y: FatoProducao[Turmas no período])
  - tableEx — Detalhe (Values: Campos_Adicionais_Diagnostico[Campo], FatoProducao[Turmas no período], FatoProducao[H/A Prevista no Painel], FatoProducao[Matrículas Previstas])

### NV05 🟠 Qualidade dos dados e pendências
- **Pergunta que responde:** O que está impedindo o número de ser confiável?
- **Por quê:** 8 medidas de pendência/validação no modelo; reuni-las orienta a correção na origem.
- **Princípio:** L4 Foco no que exige ação · [Nielsen 9] · **Auto:** sim · spec: `specs/NV05.json`
- **Visuais:**
  - card — Competências com pendência (Values: FatoProducao[Competências com pendência])
  - card — Turmas com período inválido (Values: FatoProducao[Turmas com período inválido])
  - card — Pendências de cálculo (Values: FatoProducao[Pendências de cálculo])
  - card — Turmas distintas com pendência (Values: FatoProducao[Turmas distintas com pendência])
  - tableEx — Pendências por Unidade (Values: DimUnidade[Unidade], FatoProducao[Competências com pendência], FatoProducao[Turmas com período inválido], FatoProducao[Pendências de cálculo], FatoProducao[Turmas distintas com pendência], FatoProducao[Turmas sem método no período])

### NV06 🟠 Ficha (drill-through) de DimTurma
- **Pergunta que responde:** Qual é a situação completa de um(a) DimTurma específico(a)?
- **Por quê:** DimTurma[TurmaID] identifica a entidade; uma página de drill-through tira detalhe das páginas gerenciais. Depois de gerar, configure o drill-through no Desktop (campo em 'Drill-through').
- **Princípio:** [Shneiderman] Detalhe sob demanda · **Auto:** sim · spec: `specs/NV06.json`
- **Visuais:**
  - card — Turmas no período (Values: FatoProducao[Turmas no período])
  - card — H/A Prevista no Painel (Values: FatoProducao[H/A Prevista no Painel])
  - card — Matrículas Previstas (Values: FatoProducao[Matrículas Previstas])
  - tableEx — Ficha de DimTurma (Values: DimTurma[TurmaID], DimTurma[Curso], DimTurma[MetodoEvasao], DimTurma[Status], FatoProducao[Turmas no período], FatoProducao[H/A Prevista no Painel], FatoProducao[Matrículas Previstas])

### NV07a 🟡 Tema não explorado: Melhorias\Metas
- **Pergunta que responde:** O que as medidas de 'Melhorias\Metas' mostram?
- **Por quê:** Nenhuma das 1 medidas da pasta 'Melhorias\Metas' está no relatório.
- **Princípio:** L1 Contexto · **Auto:** sim · spec: `specs/NV07a.json`
- **Visuais:**
  - card — Meta H/A no novo recorte (Values: FatoProducao[Meta H/A no novo recorte])
  - clusteredBarChart — Meta H/A no novo recorte por Unidade (Category: DimUnidade[Unidade]; Y: FatoProducao[Meta H/A no novo recorte])

### NV08 🟡 Relação entre Turmas no período e H/A Prevista no Painel
- **Pergunta que responde:** Unidades com mais Turmas no período também têm mais H/A Prevista no Painel?
- **Por quê:** Gráfico de dispersão revela atípicos; exige habilidade de dispersão no gerador (ver roadmap).
- **Princípio:** L2 Dispersão para relação · **Auto:** parcial
- **Visuais:**
  - scatterChart — Turmas no período × H/A Prevista no Painel por Unidade (Category: DimUnidade[Unidade]; X: FatoProducao[Turmas no período]; Y: FatoProducao[H/A Prevista no Painel])

### NV09 🟡 Página de dica de ferramenta
- **Pergunta que responde:** Que contexto o usuário quer ao passar o mouse?
- **Por quê:** Tooltip de página dá contexto sem ocupar espaço; configurar como Dica de ferramenta no Desktop.
- **Princípio:** L3 Menos desordem · [Shneiderman] · **Auto:** sim · spec: `specs/NV09.json`
- **Visuais:**
  - card — Turmas no período (Values: FatoProducao[Turmas no período])
  - card — H/A Prevista no Painel (Values: FatoProducao[H/A Prevista no Painel])
  - card — Matrículas Previstas (Values: FatoProducao[Matrículas Previstas])

## Títulos atuais (para reescrever como títulos de ação)

- **Visão Gerencial:** “GAP H/A” · “Meta H/A” · “Última atualização” · “Produção calculada por modalidade (H/A)” · “Ano” · “Modalidade” · “Horas descontadas pelo calendário” · “Planejamento” · “Planejamento de Turmas | Produção H/A” · “Turmas em execução” · “Financiamento” · “Produção calculada por mês (H/A)”
- **Detalhamento e Validação:** “Memória de cálculo mensal” · “Unidade” · “Ano” · “Pendências de cálculo — horários ou dados a corrigir” · “Modalidade” · “Produção por turma e competência” · “Planejamento”
- **Mobilização e oferta:** “Ano da produção” · “Modalidade” · “Oferta por mobilização e unidade” · “Mobilização” · “Matrículas previstas” · “Distribuição das turmas e H/A parcial por mobilização. Não há meta rateada por m” · “Mobilização e oferta” · “H/A parcial por mobilização” · “Turmas por mobilização” · “Unidade” · “Turmas no período (não canceladas)” · “H/A prevista parcial”
- **Oferta e capacidade:** “Ocupação prevista” · “Tipo de mediação” · “Oferta e capacidade” · “Área” · “Turmas por situação” · “Saldo previsto de vagas” · “Situação da turma” · “Vagas e matrículas previstas por unidade” · “Capacidade e matrículas previstas. A ocupação é uma previsão; não representa mat” · “Detalhamento da oferta” · “Ano da produção” · “Matrículas previstas”
- **Prontidão e pendências:** “Prontidão e pendências” · “Ano da produção” · “Método de evasão” · “Turmas distintas e competências são contagens diferentes. Método de evasão pode ” · “Modalidade” · “Unidade” · “Turmas sem horário ativo” · “Mobilização” · “Turmas sem método de evasão por unidade” · “Competências prontas (%)” · “Pendências por turma e competência — filtre a coluna Pendência” · “Competências com pendência”
- **Evasão e memória de cálculo:** “Horas descontadas pelo calendário” · “Competência” · “Turmas no período” · “Ano da produção” · “Unidade” · “Turmas sem método de evasão” · “Matrículas consideradas são mensais. Evadidos acumulados não devem ser somados e” · “Média mensal de alunos considerados” · “Turma” · “Turmas por método de evasão” · “Média mensal de alunos considerados” · “Evasão e memória de cálculo”
- **Cadastro e classificação contábil:** “Turmas no período” · “Item contábil, centro de custo e classe de valor são códigos de classificação, n” · “Classe de valor” · “Unidade” · “Cadastro e classificação contábil” · “Classificação por turma” · “H/A prevista parcial” · “Matrículas previstas” · “Vagas previstas” · “Ano da produção” · “Item contábil” · “Centro de custo”

## Perguntas de contexto (L1)

1. Quem usa o painel e que decisão toma com ele?
2. Qual é a grande ideia que a primeira página precisa transmitir?
3. Com que frequência é consultado e em qual tela (monitor, projetor, celular)?
4. Quais páginas são de conferência/exportação e podem continuar densas?
