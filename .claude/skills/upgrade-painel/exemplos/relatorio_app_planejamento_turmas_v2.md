# Análise de UX do app — App_Planejamento_Turmas_UX_v2

11 telas · 485 controles · fontes de dados: UsuáriosdoOffice365, Planejamentos, Turmas_Planejadas, Turma_Horarios, Turma_Evasao_Mensal, Cad_Unidades, Cad_Periodos_Letivos, Cad_Matrizes, Cad_Turnos, Cad_Financiamentos, Cad_Campus_Polo, Matriz_Unidade_Configuracao, CustomGallerySample, ComboBoxSample, Meta_Producao, Parametros_Evasao_Unidade, DropDownSample, Cad_Calendario, SGE, Tabela2

Referências: Nielsen, WCAG 2.2, boas práticas do Power Apps e *Storytelling com Dados* (L4/L5). Heurísticas estáticas: confirme no Power Apps Studio.

## Telas

| Tela | Controles |
|---|---|
| scrTurmas | 20 |
| scrComplementosTurma | 36 |
| scrHorarioTurma | 64 |
| scrEvasaoMensal | 58 |
| scrCadastroTurma | 152 |
| scrPlanejamentos | 19 |
| scrCadastroPlanejamento | 48 |
| scrInicio | 6 |
| scrParametrosEvasao | 22 |
| scrIndicadores | 9 |
| scrCalendarioEP | 51 |

## Melhorias sugeridas

### A01 🟠 Tela com muitos controles — scrCadastroTurma
- **Por quê:** scrCadastroTurma: 152 controles.
- **O que fazer:** Dividir a tela, usar galerias/componentes e remover controles ocultos.
- **Princípio:** [Microsoft] Desempenho de apps · `PA06`

### A02 🟠 Possível consulta não delegável — scrEvasaoMensal, scrCadastroPlanejamento
- **Por quê:** 2 telas. scrEvasaoMensal: DataCardValue6.SearchItems (ComboBoxSample: Search), DataCardValue2.SearchItems (ComboBoxSample: Search) | scrCadastroPlanejamento: DataCardValue10.SearchItems (Cad_Unidades: Search)
- **O que fazer:** Funções como in/Len/Lower/Text dentro de Filter/LookUp sobre a fonte podem limitar a 500/2000 linhas. Reescrever com operadores delegáveis ou pré-filtrar por coluna indexada.
- **Princípio:** [Microsoft] Delegação · `PA09`

### A03 🟠 Cores fixas espalhadas pelo app
- **Por quê:** 24 definições de cor diferentes nas fórmulas.
- **O que fazer:** Centralizar a paleta em App.Formulas (ex.: corPrimaria = ColorValue("#0072CE")) e referenciar nos controles.
- **Princípio:** L4 Cor consistente · [Nielsen 4] · `PA13`

### A04 🟡 Fontes pequenas — scrTurmas, scrComplementosTurma, scrHorarioTurma, scrCadastroTurma
- **Por quê:** 4 telas. scrTurmas: Label5_1 (10) | scrComplementosTurma: lblSubtituloSecaoHorarios (10), lblSubtituloSecaoEvasao (10) | scrHorarioTurma: Label4 (8) | scrCadastroTurma: cmbPlanejamento (10), txtMatriculasReais (9)
- **O que fazer:** Usar ao menos 12–13 pt em textos de leitura, sobretudo no celular.
- **Princípio:** L5 Acessibilidade · `PA03`

### A05 🟡 Alvos de toque pequenos — scrComplementosTurma, scrHorarioTurma, scrEvasaoMensal, scrCadastroTurma, scrParametrosEvasao, scrCalendarioEP
- **Por quê:** 6 telas. scrComplementosTurma: btnAbaEvasao (113.0×39.0), btnAbaProducao (113.0×38.0), btnConfigurarTaxaConvencional (238.0×36.0) | scrHorarioTurma: tglUsarUltimoHorario (154.0×29.0), DataCardValue23 (200.0×33.0) | scrEvasaoMensal: DataCardValue7 (170.0×33.0) | scrCadastroTurma: tglMatriculasReaisConfirmadas (220.0×28.0) | …
- **O que fazer:** Manter botões/ícones com ao menos 40–44 px de altura e largura.
- **Princípio:** [WCAG 2.5.8] Área de toque · `PA04`

### A06 🟡 Controles com nome padrão — scrTurmas, scrHorarioTurma, scrPlanejamentos, scrParametrosEvasao
- **Por quê:** 4 telas. scrTurmas: 9 (ex.: Image2_6, Label1, HtmlText2, Label5, Label5_1) | scrHorarioTurma: 7 (ex.: Image2_3, HtmlText10, HtmlText9, Label3, Label4) | scrPlanejamentos: 6 (ex.: Image2, Label12, Button9_1, HtmlText1, Image4) | scrParametrosEvasao: 7 (ex.: Image2_8, HtmlText14, Label7, Label7_1, Label8)
- **O que fazer:** Renomear com prefixo e função (btnSalvar, lblTitulo, galTurmas).
- **Princípio:** Convenção de nomes Power Apps · `PA05`

### A07 🟡 Layout com posições fixas — scrTurmas, scrComplementosTurma, scrInicio, scrParametrosEvasao
- **Por quê:** 4 telas. scrTurmas: 50 posições fixas em X/Y/Width; nenhum contêiner de layout automático. | scrComplementosTurma: 94 posições fixas em X/Y/Width; nenhum contêiner de layout automático. | scrInicio: 15 posições fixas em X/Y/Width; nenhum contêiner de layout automático. | scrParametrosEvasao: 61 posições fixas em X/Y/Width; nenhum contêiner de layout automático.
- **O que fazer:** Usar contêineres horizontais/verticais ou fórmulas baseadas em Parent.Width.
- **Princípio:** [Nielsen 4] · Responsividade · `PA10`

