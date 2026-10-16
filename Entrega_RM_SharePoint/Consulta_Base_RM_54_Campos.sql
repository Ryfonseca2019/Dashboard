-- CONSULTA DE INTEGRAÇÃO: somente leitura; mapeamento de campos ainda parcial.
-- Mantém os 54 nomes do CSV como contrato provisório de saída.
-- NULL identifica campo ainda não mapeado; não significa apagar a lista.
-- Tipos dos campos pendentes são provisórios, não são tipos SharePoint confirmados.
-- Este SQL reutiliza origens do PBIP, mas ainda NÃO foi executado no RM.
DECLARE @FimAPartirDe date = DATEFROMPARTS(YEAR(GETDATE()), 1, 1); -- início do ano atual no servidor RM

SELECT
    CAST(NULL AS nvarchar(4000)) AS [Planejamento], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Unidade], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    P.CODPERLET AS [Periodo_Letivo], -- origem presente no SQL fornecido; validar semântica
    CAST(NULL AS int) AS [Ano_Referencia], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Identificador_Temporario], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    T.CODTURMA AS [Codigo_Turma_SGE], -- origem presente no SQL fornecido; validar semântica
    CAST(NULL AS nvarchar(4000)) AS [Matriz], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Status_Turma], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS bit) AS [Ativa], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Codigo_Matriz_Snapshot], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    C.NOME AS [Nome_Curso_Snapshot], -- origem presente no SQL fornecido; validar semântica
    CAST(NULL AS nvarchar(4000)) AS [Area_Snapshot], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Modalidade_Snapshot], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Tipo_Mediacao_Snapshot], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS decimal(18,4)) AS [Carga_Horaria_Snapshot], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS datetime2) AS [Data_Snapshot_Matriz], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    T.DTINICIAL AS [Data_Inicio_Prevista], -- origem presente no SQL fornecido; validar semântica
    T.DTFINAL AS [Data_Fim_Prevista], -- origem presente no SQL fornecido; validar semântica
    T.MAXALUNOS AS [Quantidade_Vagas], -- origem presente no SQL fornecido; validar semântica
    CAST(NULL AS int) AS [Matriculas_Previstas], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Campus_Polo], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Financiamento], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Tipo_Periodo], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Pedagogo_Responsavel], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Mobilizacao], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Empresa], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Projeto], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Sindicato], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Classe_Valor], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Item_Contabil_Snapshot], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Centro_Custo_Snapshot], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Observacoes], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Motivo_Cancelamento], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS datetime2) AS [Data_Cancelamento], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Cancelada_Por], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS datetime2) AS [Data_Conclusao], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS bit) AS [Bloqueada_Para_Edicao], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS int) AS [Versao_Planejamento], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Origem_Registro], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS datetime2) AS [Data_Ultima_Revisao], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Turno], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Tipo_Calculo_Evasao], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS decimal(18,4)) AS [Percentual_Evasao_Previsto], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS decimal(18,4)) AS [Quantidade_Evasao_Prevista], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS decimal(18,4)) AS [Matriculas_Consideradas], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS int) AS [ID], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS int) AS [Matriculas_Reais], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS bit) AS [Matriculas_Reais_Confirmadas], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Código da turma SGE], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Local_realizacao], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Instrutor], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Codigo_Matriz_Excel], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS datetime2) AS [Criado], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    CAST(NULL AS nvarchar(4000)) AS [Criado por], -- PENDENTE: não enviar NULL para sobrescrever valores existentes
    -- Colunas técnicas adicionais: preservar no estágio de integração.
    T.CODCOLIGADA AS [RM_CODCOLIGADA],
    T.CODFILIAL AS [RM_CODFILIAL],
    T.IDPERLET AS [RM_IDPERLET],
    T.CODTURMA AS [RM_CODTURMA],
    F.NOME AS [RM_Unidade_Nome],
    F.NOMEFANTASIA AS [RM_Unidade_Fantasia],
    H.CODGRADE AS [RM_Codigo_Grade],
    H.CODCURSO AS [RM_Codigo_Curso],
    C.CODMODALIDADECURSO AS [RM_Codigo_Modalidade_Curso],
    T.MODALIDADE AS [RM_Modalidade_Turma],
    T.CODCAMPUS AS [RM_Codigo_Campus],
    T.CODCCUSTO AS [RM_Centro_Custo],
    T.IDITEMCONTABILPROTHEUS AS [RM_Item_Contabil],
    T.TURMAENCERRADA AS [RM_Turma_Encerrada]
FROM dbo.STURMA AS T
LEFT JOIN dbo.SPLETIVO AS P
    ON P.CODCOLIGADA = T.CODCOLIGADA AND P.IDPERLET = T.IDPERLET
LEFT JOIN dbo.GFILIAL AS F
    ON F.CODCOLIGADA = T.CODCOLIGADA AND F.CODFILIAL = T.CODFILIAL
LEFT JOIN dbo.SHABILITACAOFILIAL AS H
    ON H.CODCOLIGADA = T.CODCOLIGADA
    AND H.IDHABILITACAOFILIAL = T.IDHABILITACAOFILIAL
LEFT JOIN dbo.SCURSO AS C
    ON C.CODCOLIGADA = H.CODCOLIGADA AND C.CODCURSO = H.CODCURSO
WHERE T.DTFINAL >= @FimAPartirDe
ORDER BY T.CODCOLIGADA, T.CODFILIAL, T.IDPERLET, T.CODTURMA;

-- A chave de turma e a cardinalidade dos joins são provisórias.
-- Resolver descrições/domínios e agregar matrículas e instrutores antes de adicioná-los.
-- Sem limite de linhas e sem filtro de início. Término no ano atual ou posterior; términos nulos ficam de fora.
