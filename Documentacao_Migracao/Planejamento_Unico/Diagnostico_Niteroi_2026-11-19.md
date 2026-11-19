# Diagnóstico | Niterói e planejamento único por unidade

Data: 19/11/2026. Fontes analisadas:

- `App_Planejamento_Turmas_Desenvolvimento_5.msapp`, salvo em 19/11/2026 às 19:16 UTC. O código das telas é idêntico ao Desenvolvimento_4.
- Exportações do SharePoint:
  - `Planejamentos` (69 linhas);
  - `Turmas_Planejadas` (1.993);
  - `Cad_Periodos_Letivos` (509);
  - `Parametros_Evasao_Unidade` (173).

As exportações não trazem os IDs dos itens nem dos vínculos. As conclusões que dependem de ID estão marcadas como inferência.

## Conclusão

O app já permite gravar uma turma de 2027 em Niterói. Em 17/11 às 10:56, a turma `NIT-20261117105642` foi gravada pelo app: Técnico em Edificações, período 2027.1, ano 2027, evasão convencional de 20%. Às 12:06 a mesma usuária a desativou, o que equivale a excluir pelo app. O motivo precisa ser confirmado com a unidade.

A dificuldade relatada vem dos dados:

1. Niterói tem três planejamentos ativos.
2. A tela abre um planejamento chamado "2026" para cadastrar 2027.
3. Os períodos letivos de 2027 aparecem duplicados.

## Evidências | Niterói

| Planejamento | Ano | Criado em | Turmas ativas | Turmas inativas |
| --- | --- | --- | --- | --- |
| Planejamento Niterói | 2026 | 08/10 | 111 | 3 |
| Planejamento Niterói 2027 | 2027 | 08/10 | 0 | 0 |
| Planejamento Niterói 2026 | 2026 | 21/10 | 5 | 1 (a turma de 2027) |

- **Planejamento que o app abre:** `scrPlanejamentos` › `galPlanejamentosHorizontal` agrupa por `Unidade.Id` e mostra só o planejamento de maior ID. Pela data de criação, inferimos que seja o "Planejamento Niterói 2026". As turmas gravadas pelo app em 14/11 e 17/11 estão nele, o que confirma a inferência.
- **Turmas exibidas:** `scrTurmas` › `Gallery1` filtra por `Unidade.Id` e mostra as 116 turmas ativas, que estão em dois planejamentos.
- **Períodos de 2027 em dobro:** `Cad_Periodos_Letivos` tem Niterói 2027, 2027.1 e 2027.2 duas vezes.
- **Taxas de evasão de 2027 cadastradas:**

  | Modalidade | Taxa |
  | --- | --- |
  | AIB | 15% |
  | AITNM | 15% |
  | HTNM | 20% |
  | QP | 20% |
  | Aperfeiçoamento/Especialização | 10% |

  Não há duplicatas. Falta Iniciação Profissional 2027, caso a unidade oferte.
- **Ano incoerente com o período:** a turma `NIT-20261008201200` (inativa, observação "Teste") tem período 2026 e ano 2027.

## Evidências | Demais unidades

- **Planejamentos:** 69 planejamentos ativos para cerca de 30 unidades. A maioria tem planejamentos separados para 2025, 2026 e 2027. A migração para o planejamento único atinge todas as unidades.
- **Períodos duplicados:** 60 combinações de unidade e período estão duplicadas em `Cad_Periodos_Letivos`:

  | Período | Unidades com duplicata |
  | --- | --- |
  | 2026.2 | 27 |
  | 2027 | 12 |
  | 2027.1 | 11 |
  | 2027.2 | 10 |

  Itaguaí e Três Rios não têm 2027.1.
- **Ano "2" na carga:** 38 turmas da carga de 21/10 (`Origem_Registro = Importação`) têm `Ano_Referencia = 2`. São Barra do Piraí (28), Pádua (9) e Niterói (1, inativa). O valor "2.026" foi lido como 2 na importação.
- **Taxas de evasão:** nenhuma turma convencional ativa está sem taxa correspondente (unidade, ano e modalidade). `Chave_Parametro` é coerente em todos os registros.

## Plano para Niterói (piloto da migração)

1. Exportar com IDs:
   - `Planejamentos`: ID;
   - `Turmas_Planejadas`: ID, `Planejamento:ID` e `Periodo_Letivo:ID`;
   - `Cad_Periodos_Letivos`: ID.
2. Definir o planejamento canônico. Proposta: "Planejamento Niterói", que tem 111 turmas.
3. Gerar a planilha de/para (ID antigo → ID canônico) e mover as 6 turmas do "Planejamento Niterói 2026". Conferir as contagens antes e depois.
4. Desativar (`Ativo = false`, sem excluir) o "Planejamento Niterói 2026" e o "Planejamento Niterói 2027". O cartão da unidade passa a abrir o canônico.
5. Nos períodos duplicados, desativar a cópia sem turmas vinculadas. Se as duas cópias tiverem turmas, mover os vínculos para a de menor ID antes de desativar.
6. Validar com a unidade:
   - cadastrar de novo a turma de 2027;
   - conferir a lista de turmas e o BI.
7. Reversão: guardar a planilha de/para e as exportações originais. Os passos usam apenas atualização de vínculo e de `Ativo`, sem exclusão.

## Ajustes no app

Fórmulas completas em `Formulas_Ajustes_App_v5.txt`:

1. `cmbPeriodoLetivo`: filtra pelo ID da unidade, elimina períodos repetidos e passa a exibir o campo `Periodo_Letivo`.
2. `txtAnoReferencia` e `Ano_Referencia_DataCard1`: o ano vem do período letivo escolhido.
3. `Title2` e `Subtitle2` no cartão do planejamento: mostram o nome e alertam quando a unidade tem mais de um planejamento ativo.

## Pendências

- Confirmar com Niterói por que a turma de 2027 foi desativada.
- Confirmar a regra de negócio: o ano de referência da turma é o ano do período letivo.
- Corrigir as 38 turmas com ano "2", depois de conferir o período de cada uma.
- Mapear no Power BI os usos de `Ano_Planejamento` e de `Planejamento` antes de desativar planejamentos.
