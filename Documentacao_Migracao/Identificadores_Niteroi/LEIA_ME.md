# Identificadores de Niterói — 103 turmas

Regra encontrada no app, na ação de salvar nova turma:

```powerfx
LookUp(Cad_Unidades, ID = cmbUnidade.Selected.Id, Sigla_UNOP)
    & "-" & Text(Now(), "yyyymmddhhmmss")
```

O prefixo NIT foi confirmado por um item anterior de Niterói no CSV SharePoint recebido. O app calcula a sigla pelo cadastro Cad_Unidades; o valor cadastral não foi consultado ao vivo.

Para o lote foram gerados 103 valores no mesmo formato, com um segundo de diferença entre linhas para evitar duplicações no mesmo segundo. Os horários são de geração para importação, não datas históricas de criação das turmas. A ordem das linhas é a mesma do arquivo recebido, sem ordenar ou filtrar. Foram preservados os demais campos.

## Como colar

Baixe Identificadores_Niteroi_103_linhas.xlsx. Copie A2:A104 e cole na coluna Identificador_Temporario das mesmas 103 linhas, na ordem original. O arquivo TXT fornece os mesmos valores sem cabeçalho. Se a ordem das turmas mudar, não cole a coluna isolada: use a planilha completa preenchida ou reconcilie por turma.

O CSV e XLSX completos foram preparados no ambiente, mas não publicados no GitHub porque contêm os dados recebidos, incluindo nomes de instrutores. Aqui estão somente os identificadores gerados.

## Cuidados encontrados no app

A galeria filtra `Ativa = true` e `Planejamento.Value = varPlanejamentoSelecionado.Nome_Planejamento`. A planilha recebida está com Ativa vazia nas 103 linhas. Para que sejam exibidas, atribua Sim/True conforme a coluna booleana e vincule ao planejamento correto. O arquivo preenchido altera apenas Identificador_Temporario; não altera Ativa nem outros dados.

O app inicializa Ativa=true, Bloqueada_Para_Edicao=false e Versao_Planejamento=1 quando cria uma nova turma. A inclusão pela grade não executa essas fórmulas: confira esses campos e os demais obrigatórios na lista.

Os valores são únicos no lote e não coincidem com identificadores das exportações usadas como referência; a lista SharePoint completa não foi consultada. Reutilize o mesmo arquivo em novas tentativas para evitar gerar novos identificadores para a mesma turma. Não foi realizada inclusão no SharePoint.
