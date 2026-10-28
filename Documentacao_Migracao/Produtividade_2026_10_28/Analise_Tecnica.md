# Análise do painel de produtividade — 28/10/2026

A análise foi feita sobre o modelo efetivamente salvo no PBIX, e não apenas nos scripts TMDL de rascunho que ele contém. Não houve atualização das fontes.

## Fotografia do arquivo recebido

- Duas páginas: Visão Gerencial e Detalhamento e Validação.
- Onze tabelas carregadas, dez relacionamentos, 25 medidas DAX e onze expressões auxiliares/funções.
- 1.492 turmas: 1.482 ativas e dez inativas; 69 planejamentos e 32 unidades.
- 18.146 registros turma/competência, sem repetição da chave TurmaID + Competencia, entre fevereiro/2025 e dezembro/2029.
- 12.928 competências com cálculo inválido. Há 1.055 turmas distintas com alguma competência inválida. Essas contagens não devem ser tratadas como a mesma unidade de medida.
- Motivos mensais: 12.368 registros com horário e método ausentes; 480 apenas com método ausente; 80 apenas sem horário ativo. O primeiro grupo participa dos dois problemas; não somar categorias como turmas distintas.
- Métodos em DimTurma: 1.046 vazios, 417 Convencional e 29 Manual mensal.
- Financiamento: 1.153 Gratuidade, 202 Negócio PJ e 137 Negócio, preservados separadamente.
- Duas metas ativas, ambas de 2026 para UnidadeID 5, por financiamento. Não há meta de 2027 no cache recebido.
- Três referências a planejamentos não encontrados na dimensão, duas em turmas ativas. Verificar origem do vínculo, sem presumir que sejam todos cadastros reais ou todos testes.
- Todos os períodos da dimensão passam no teste atual de datas (início/fim). Isso não valida carga de horários ou regras de calendário.
- Atualizacao registra 28/10/2026 14:10 UTC (11:10 no horário de Brasília).

## Mobilização

A coluna não está no modelo carregado porque DimTurma usa Table.SelectColumns e a elimina. O dado não pode ser recuperado do cache do PBIX sem atualizar a consulta. A proposta adiciona Mobilizacao usando a função existente fxTexto e uma dimensão de valores distintos, com relação 1:N para DimTurma. Não inventa códigos RM nem junta opções diferentes do SharePoint.

A granularidade de FatoProducao permanece turma/mês. Mobilização entra na dimensão da turma, evitando expandir uma linha da produção em várias. Se a fonte passar a permitir mais de uma mobilização por turma, fxTexto deverá ser revista e a relação deverá ser modelada por uma tabela-ponte; não concatenar nem multiplicar os fatos sem regra de atribuição.

## Preservação e proposta

As 25 expressões DAX originais foram preservadas. Também foram preservados, byte a byte, os arquivos das duas páginas e de seus visuais. A cópia editável adiciona quatro páginas, dez campos em DimTurma, uma dimensão, uma tabela de auditoria e treze medidas.

A regra de cálculo da H/A não foi alterada: produção parcial continua sendo a soma das competências calculáveis, e produção integral continua condicionada às pendências. Novas medidas distinguem turmas distintas de competências, e a cobertura desconsidera competências canceladas.

O rótulo original Turmas em Execução abrange turmas não canceladas com competências no período, incluindo rascunhos/planejadas. Por isso as páginas novas usam Turmas no período, sem alterar a medida original.

## Pontos para validação de negócio

- Carga calculada versus carga da matriz: 292 turmas apresentaram carga letiva acumulada maior que a carga de matriz positiva no diagnóstico inicial. Investigar calendário, vigência, horário e tolerância. É alerta, não conclusão de erro ou autorização para limitar a produção.
- Evasão manual: a função atual pode tratar ausência de registro mensal como zero de evasão. Confirmar se isso é a regra desejada; não mudar silenciosamente.
- Evasão convencional: a taxa é buscada pelo ano de referência da turma, não por cada ano de competência. Confirmar o tratamento de cursos que atravessam anos.
- Calendário: a função usa apenas o dia inicial se DataUnica=true, mesmo com fim preenchido. Conferir dados do aplicativo para intervalos de férias/recesso.
- Mobilização, área, mediação e turno não têm metas específicas. Não distribuir metas por conta própria.
- A ocupação proposta usa matrículas PREVISTAS / vagas PREVISTAS, sem representar efetivação. Saldo negativo deve ser investigado; não é truncado para zero.
- Ano do planejamento e ano da produção são conceitos diferentes; filtros das páginas novas usam DimAno (competência da produção).

## Desempenho

A fonte do painel é SharePoint. Não foi adicionada conexão ao RM. As consultas de staging e funções são expressões auxiliares, não onze conexões novas por esse motivo. Contudo, consultas dependentes podem reavaliar a origem durante a atualização; Table.Buffer não garante uma única chamada global.

A função atual varre horários/evasões por turma e parâmetros/calendário repetidamente. Uma próxima etapa é indexar/grupar essas entradas, medir o tempo de atualização e comparar a produção linha a linha com a regra atual. Essa refatoração não foi incluída nesta versão para preservar o comportamento.

## Homologação proposta

1. Abrir o PBIP novo em pasta separada; não substituir o PBIX em uso.
2. Atualizar com acesso ao SharePoint e revisar Campos_Adicionais_Diagnostico.
3. Comparar as duas páginas originais, sob os mesmos filtros e mesma fonte, com a versão atual.
4. Conferir três mobilizações conhecidas, um caso sem mobilização, uma turma multianual, uma cancelada, uma com evasão convencional e uma manual.
5. Conferir que somar turmas por mês repete uma turma multianual; usar o total distinto da medida, não soma de contagens mensais.
6. Verificar horas descontadas por férias e feriados e conferir duplicidades de horários.
7. Validar nomes de campos, credenciais e aparência no Desktop. Só depois publicar em espaço de teste.

O tema customizado mencionado pelo relatório não foi incluído no PBIX. A cópia utiliza o tema base embutido, preservando os objetos dos visuais, mas cores derivadas do tema podem variar. Para identidade exata, importar o JSON original do tema.

## Escopo da entrega

A planilha e este relatório são conclusões sobre o arquivo recebido. O PBIP é uma implementação preparada para homologação, sem dados em cache, e precisa de atualização. A disponibilidade e o preenchimento dos campos extras no SharePoint atual só serão confirmados nessa atualização. Nenhum dado ou relatório publicado foi modificado.
