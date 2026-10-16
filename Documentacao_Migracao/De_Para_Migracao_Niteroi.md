# De/para RM → SharePoint — Niterói

Comparação das exportações recebidas: **103 linhas RM**, com 103 chaves compostas distintas, e **12 linhas SharePoint**. São **54 campos de destino**. Somente seis campos de destino têm dados preenchidos no arquivo RM; os outros 48 são cabeçalhos sem valores. Há ainda quatro campos técnicos preenchidos.

Não há códigos de turma coincidentes entre os dois arquivos. Isso não comprova que as turmas sejam novas na lista inteira: a exportação SharePoint pode ser parcial. Conferir a lista completa antes de inserir.

O arquivo RM possui 102 inícios em 2026 e um em 2025; 76 términos em 2027 e 27 em 2028. Portanto, não contém términos de 2026. Reexportar a consulta V5 se a migração deve incluir todo o ano atual em diante; não é possível saber pelo CSV se existem outros registros no banco.

## Contrato por campo

Os cabeçalhos abaixo são nomes exibidos no CSV; não comprovam nomes internos da API nem tipos reais do SharePoint.

| Campo SharePoint | Origem | Classificação | Regra |
|---|---|---|---|
| Planejamento | Cadastro de planejamentos do app | Vínculo obrigatório a confirmar | Escolher planejamento de destino por regra de negócio. Não inferir a partir do ano de início, término ou período; se Lookup, resolver ID. O exemplo Niterói aponta Planejamento Niterói 2027, mas não autoriza aplicar esse planejamento às 103 turmas. |
| Unidade | RM_Unidade_Nome + RM_CODCOLIGADA + RM_CODFILIAL | Equivalência identificada | Para coligada 3 e filial 266, SENAI Niterói corresponde a Niterói no exemplo SharePoint. Se Lookup, usar ID do cadastro de unidades, não apenas texto. |
| Periodo_Letivo | Periodo_Letivo | Direto | Preservar texto; não converter códigos em número. Validar tipo e nome interno do campo SharePoint. |
| Ano_Referencia | Planejamento de destino | Regra de negócio | Usar o ano do planejamento aprovado. Não derivar automaticamente do início/fim. Valores exportados 2.026 e 2.027 representam 2026 e 2027; gravar conforme tipo da coluna. |
| Identificador_Temporario | Chave RM composta | Proposta de identificador | Proposta: RM-{RM_CODCOLIGADA}-{RM_CODFILIAL}-{RM_IDPERLET}-{Codigo_Turma_SGE}. Confirmar que o app aceita esse formato. Preferível guardar chave em campo próprio de integração para migrações repetidas. |
| Codigo_Turma_SGE | Codigo_Turma_SGE | Direto | Preservar texto; não converter códigos em número. Validar tipo e nome interno do campo SharePoint. |
| Matriz | Cadastro de matrizes + vínculo RM não exportado | Cadastro pendente | Obter código de matriz e equivalência com cadastro do app. Não extrair do prefixo do código da turma. Se Matriz for Lookup, usar ID da matriz no SharePoint. |
| Status_Turma | Regra do app ou estado RM não exportado | Pendente | Não inferir Planejada só porque o arquivo se chama Planejadas. Rascunho é opção observada para cadastro incompleto; confirmar se fica visível no app e se a transição é permitida. |
| Ativa | Regra de negócio / estado RM | Pendente | True é observado na lista, não é evidência do estado de cada turma RM. Definir antes da carga. |
| Codigo_Matriz_Snapshot | Cadastro de matrizes + vínculo RM não exportado | Cadastro pendente | Obter código de matriz e equivalência com cadastro do app. Não extrair do prefixo do código da turma. Se Matriz for Lookup, usar ID da matriz no SharePoint. |
| Nome_Curso_Snapshot | Nome_Curso_Snapshot | Direto | Preservar texto; não converter códigos em número. Validar tipo e nome interno do campo SharePoint. |
| Area_Snapshot | Cadastro de matriz/curso validado | Cadastro pendente | Não disponível no CSV RM. Buscar na matriz correspondente; garantir a mesma origem para todos os snapshots. Carga horária deve ser numérica, não texto com separadores. |
| Modalidade_Snapshot | Cadastro de matriz/curso validado | Cadastro pendente | Não disponível no CSV RM. Buscar na matriz correspondente; garantir a mesma origem para todos os snapshots. Carga horária deve ser numérica, não texto com separadores. |
| Tipo_Mediacao_Snapshot | Cadastro de matriz/curso validado | Cadastro pendente | Não disponível no CSV RM. Buscar na matriz correspondente; garantir a mesma origem para todos os snapshots. Carga horária deve ser numérica, não texto com separadores. |
| Carga_Horaria_Snapshot | Cadastro de matriz/curso validado | Cadastro pendente | Não disponível no CSV RM. Buscar na matriz correspondente; garantir a mesma origem para todos os snapshots. Carga horária deve ser numérica, não texto com separadores. |
| Data_Snapshot_Matriz | Momento da captura da matriz | Gerado na carga | Preencher somente quando os dados da matriz forem efetivamente capturados; não usar data de início da turma. |
| Data_Inicio_Prevista | Data_Inicio_Prevista | Conversão | Interpretar yyyy-MM-dd HH:mm:ss como data; gravar sem deslocar o dia. Confirmar se coluna SharePoint é somente data ou data/hora. |
| Data_Fim_Prevista | Data_Fim_Prevista | Conversão | Interpretar yyyy-MM-dd HH:mm:ss como data; gravar sem deslocar o dia. Confirmar se coluna SharePoint é somente data ou data/hora. |
| Quantidade_Vagas | Quantidade_Vagas | Conversão | Inteiro; não substituir por matrículas previstas ou reais. |
| Matriculas_Previstas | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Campus_Polo | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Financiamento | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Tipo_Periodo | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Pedagogo_Responsavel | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Mobilizacao | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Empresa | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Projeto | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Sindicato | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Classe_Valor | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Item_Contabil_Snapshot | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Centro_Custo_Snapshot | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Observacoes | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Motivo_Cancelamento | Evento real não exportado | Sem origem | Não inventar evento; preservar em atualização. Data_Fim_Prevista não equivale a Data_Conclusao. |
| Data_Cancelamento | Evento real não exportado | Sem origem | Não inventar evento; preservar em atualização. Data_Fim_Prevista não equivale a Data_Conclusao. |
| Cancelada_Por | Evento real não exportado | Sem origem | Não inventar evento; preservar em atualização. Data_Fim_Prevista não equivale a Data_Conclusao. |
| Data_Conclusao | Evento real não exportado | Sem origem | Não inventar evento; preservar em atualização. Data_Fim_Prevista não equivale a Data_Conclusao. |
| Bloqueada_Para_Edicao | Inicialização pelo aplicativo | Regra do app | Usar rotina de criação do app. Falso e versão 1 são valores observados, não regra confirmada para migração. |
| Versao_Planejamento | Inicialização pelo aplicativo | Regra do app | Usar rotina de criação do app. Falso e versão 1 são valores observados, não regra confirmada para migração. |
| Origem_Registro | Identificador de origem da migração | Proposta | Usar RM somente se aceito pelo tipo/opções e filtros do app; caso contrário, definir opção específica. Não classificar importação como Aplicativo sem decisão. |
| Data_Ultima_Revisao | Rotina de importação / revisão | Regra do app | Distinguir data de migração de revisão humana. Confirmar política; não copiar automaticamente data de atualização RM. |
| Turno | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Tipo_Calculo_Evasao | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Percentual_Evasao_Previsto | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Quantidade_Evasao_Prevista | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Matriculas_Consideradas | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| ID | SharePoint | Sistema | Na criação, deixar SharePoint gerar. Para atualizar item existente, resolver ID real da lista; nunca copiar ID RM ou inventar autoria/data de criação. |
| Matriculas_Reais | Contagem de matrículas RM não exportada | Consulta adicional | Definir situações válidas e granularidade antes de contar. Não usar Quantidade_Vagas como matrícula. |
| Matriculas_Reais_Confirmadas | Processo de confirmação do app | Regra do app | Não marcar True sem validação. Definir tratamento de valor pendente conforme lógica do aplicativo. |
| Código da turma SGE | Codigo_Turma_SGE, se necessário para compatibilidade | Coluna alternativa vazia | Está vazia em ambos os CSVs. Usar Codigo_Turma_SGE como campo principal; confirmar qual o app lê antes de replicar códigos em duas colunas. |
| Local_realizacao | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Instrutor | Sem valor na exportação RM | Enriquecimento pendente | Buscar origem no RM/cadastro ou informar no planejamento. Não preencher zero/vazio como dado confirmado. Campos Pessoa, Lookup ou Escolha exigem resolução de IDs/opções se aplicável. |
| Codigo_Matriz_Excel | Cadastro de matrizes + vínculo RM não exportado | Cadastro pendente | Obter código de matriz e equivalência com cadastro do app. Não extrair do prefixo do código da turma. Se Matriz for Lookup, usar ID da matriz no SharePoint. |
| Criado | SharePoint | Sistema | Na criação, deixar SharePoint gerar. Para atualizar item existente, resolver ID real da lista; nunca copiar ID RM ou inventar autoria/data de criação. |
| Criado por | SharePoint | Sistema | Na criação, deixar SharePoint gerar. Para atualizar item existente, resolver ID real da lista; nunca copiar ID RM ou inventar autoria/data de criação. |

## Chave e atualização

Usar como chave de integração a combinação coligada + filial + IDPERLET + código da turma. Na amostra todas são distintas. Se a mesma turma puder existir em vários planejamentos, acrescentar o ID do planejamento ao critério de correspondência. Não usar nome do curso como chave.

Na gravação, criar apenas itens sem correspondência e atualizar somente os itens de identidade confirmada. Não enviar NULLs para sobrescrever informações do app. Nenhuma carga foi executada.

## Antes da migração

1. Confirmar planejamento de destino e ano de referência: podem diferir do início/fim e do período RM.
2. Obter definição das colunas SharePoint: nome interno, tipo, obrigatoriedade, opções, listas de Lookup e Pessoa.
3. Conferir filtros do app: Planejamento, Unidade, Status_Turma, Ativa e vínculos de Matriz. CSVs não permitem comprovar as condições de exibição.
4. Completar os dados de matriz, carga horária, modalidade, financiamento e demais campos exigidos pelo app. Não assumir que os seis campos disponíveis bastam.
5. Importar primeiro uma pequena amostra validada, conferir exibição no app, então executar a carga completa com chave de integração e relatório de erros.
