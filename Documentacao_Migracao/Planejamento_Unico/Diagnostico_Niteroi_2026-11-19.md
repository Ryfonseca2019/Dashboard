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

## Execução do piloto de Niterói (com as exportações de IDs de 19/11)

### O que as exportações de IDs trouxeram

- **Cad_Unidades:** Niterói tem ID 15 e sigla NIT.
- **Turmas_Planejadas:** traz o ID de cada turma. Os vínculos de planejamento e de período continuam só como texto.
- **Planejamentos:** a exportação ainda veio sem a coluna ID.
- **Nomes de planejamento:** nenhum se repete dentro da mesma unidade. Por isso o vínculo pelo nome é inequívoco para esta migração.
- **Períodos duplicados de Niterói:**

  | Período | IDs |
  | --- | --- |
  | 2026.2 | 42 e 390 |
  | 2027 | 123 e 156 |
  | 2027.1 | 124 e 157 |
  | 2027.2 | 125 e 158 |

### Situação em 19/11

Os passos 1 e 2 foram executados e conferidos na exportação Turmas_Planejadas_13 e Planejamentos_6:

- **Planejamentos de Niterói:** o planejamento 16, "Planejamento Niterói", é o único ativo. Os planejamentos 18 e 63 foram desativados.
- **Turmas de Niterói:** todas as 120 estão no planejamento 16, sendo 116 ativas e 4 inativas.
- **Demais unidades:** nenhuma outra turma foi alterada pela migração. O total continua em 1.993.
- **Ano "2":** a turma 216, de Barra do Piraí, foi corrigida pela unidade no app, ao ser editada e salva. Restam 37 turmas com ano "2", e a turma 216 saiu do CSV de correção.

### Passo 1 | Mover as turmas para o planejamento único

Arquivo: `Niteroi_DePara_Turmas.csv`.

As turmas de ID 1917 a 1921 (ativas) e 1979 (a turma de 2027, inativa) passam de "Planejamento Niterói 2026" para "Planejamento Niterói". São 6 itens. Faça a edição em grade (Editar no modo de grade) na lista `Turmas_Planejadas`, filtrada por esses IDs.

Contagem esperada depois do passo 1:

| Planejamento | Turmas ativas | Turmas inativas |
| --- | --- | --- |
| Planejamento Niterói | 116 | 4 |
| Planejamento Niterói 2026 | 0 | 0 |
| Planejamento Niterói 2027 | 0 | 0 |

### Passo 2 | Desativar os planejamentos extras

Marcar `Ativo = Não` em "Planejamento Niterói 2026" e "Planejamento Niterói 2027". Os registros não devem ser excluídos.

Em seguida, abrir o app e conferir:

- o cartão de Niterói mostra "Planejamento Niterói";
- a lista de turmas tem 116 turmas;
- uma turma nova fica vinculada ao planejamento canônico.

### Passo 3 | Períodos duplicados

Mantenha as duas cópias ativas até saber a qual ID cada turma está ligada. O ajuste 1 do app já mostra uma só opção no combo e usa o menor ID (42, 123, 124 e 125) para as turmas novas.

Para desativar as cópias 390, 156, 157 e 158, falta exportar `Turmas_Planejadas` com a coluna `Periodo_Letivo:ID`. Ela é habilitada nas configurações da coluna Periodo_Letivo, em "campos adicionais".

### Passo 4 | Ano de referência gravado como "2"

Arquivo: `Correcao_Ano_Referencia_2.csv`.

São 38 turmas da importação de 21/10: Barra do Piraí (28), Pádua (9) e Niterói (1, inativa, ID 60). Todas estão em períodos 2026, 2026.1 ou 2026.2, então o valor correto é 2026. A correção é feita por edição em grade.

### Reversão

As exportações originais (Turmas_Planejadas_12 e Planejamentos_5) e os CSVs de/para guardam o estado anterior. Para desfazer:

1. Devolver o planejamento das 6 turmas.
2. Reativar os dois planejamentos.

### Antes de executar

- Confirmar se o Power BI filtra ou agrupa por `Planejamento` ou por `Ano_Planejamento`. Se o relatório separar a produção por planejamento, os totais por planejamento mudam, mas o total da unidade continua o mesmo.

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
