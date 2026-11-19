# Fluxo diário | Status das turmas pelas datas

Fluxo de nuvem agendado no Power Automate. Mantém o `Status_Turma` gravado no SharePoint igual à regra do app, para que o Power BI e o filtro "Situação" usem o status atualizado mesmo nas turmas que ninguém abre.

## Configuração

1. **Gatilho:** Recorrência, 1 vez por dia, às 05:00, fuso **(UTC-03:00) Brasília**.
2. **Inicializar variável** `hoje` (cadeia de caracteres): `formatDateTime(convertFromUtc(utcNow(), 'E. South America Standard Time'), 'yyyy-MM-dd')`.
3. Três blocos **SharePoint › Obter itens** na lista `Turmas_Planejadas`. Em cada um, ative a **paginação** (Configurações → Paginação → limite de 5.000) e use a **Consulta de filtro** indicada.
4. Dentro de cada bloco, um **Aplicar a cada** com **SharePoint › Atualizar item** usando `ID` = `items('Aplicar_a_cada')?['ID']` e `Status_Turma Value` = valor indicado.
   - Preencha só o status. Os campos obrigatórios que o conector pedir devem receber o próprio valor do item, por exemplo `items('Aplicar_a_cada')?['Unidade']?['Id']`.

| Bloco | Consulta de filtro (OData) | Novo status |
| --- | --- | --- |
| A. Concluídas | `Ativa eq 1 and Status_Turma ne 'Cancelada' and Status_Turma ne 'Concluída' and Data_Fim_Prevista lt '@{variables('hoje')}'` | Concluída |
| B. Em execução | `Ativa eq 1 and Status_Turma ne 'Cancelada' and Status_Turma ne 'Em execução' and Data_Inicio_Prevista le '@{variables('hoje')}' and Data_Fim_Prevista ge '@{variables('hoje')}'` | Em execução |
| C. Ainda não iniciadas | `Ativa eq 1 and (Status_Turma eq 'Em execução' or Status_Turma eq 'Concluída') and Data_Inicio_Prevista gt '@{variables('hoje')}'` | Planejada |

## Cuidados

- A opção **"Concluída"** precisa existir na coluna Escolha `Status_Turma`.
- **Primeira execução:** pelos dados de 19/11, cerca de **570 turmas** passam para Em execução e **9** voltam para Planejada. Rode primeiro numa cópia da lista, ou desative o "Atualizar item" e confira a quantidade em "Obter itens".
- **Datas com hora:** se `Data_Inicio_Prevista` e `Data_Fim_Prevista` forem do tipo Data e hora, a comparação usa UTC. Para colunas "Somente data" o filtro acima é exato.
- **Coluna "Modificado":** o fluxo altera a data de "Modificado" e o "Modificado por" das turmas. O usuário do fluxo precisa de permissão de edição na lista.
- **Consumo:** use *Concorrência* de 1 a 5 no "Aplicar a cada" para não exceder os limites do SharePoint.
