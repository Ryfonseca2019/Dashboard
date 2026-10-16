SET NOCOUNT ON;
-- CONSULTA DE INTEGRAÇÃO: somente leitura; mapeamento de campos ainda parcial.
-- Mantém os 54 nomes do CSV como contrato provisório de saída.
-- NULL identifica campo ainda não mapeado; não significa apagar a lista.
-- Tipos dos campos pendentes são provisórios, não são tipos SharePoint confirmados.
-- Este SQL reutiliza origens do PBIP, mas ainda NÃO foi executado no RM.
DECLARE @FimAPartirDe date = DATEFROMPARTS(YEAR(GETDATE()), 1, 1); -- início do ano atual no servidor RM

-- Professor é associado à oferta/disciplina, não somente ao nome do curso.
-- Os vínculos abaixo são candidatos e são verificados por metadados antes de uso.
-- A tabela temporária recebe somente os nomes e a chave da turma.
SELECT TOP (0) T.CODCOLIGADA, T.CODFILIAL, T.IDPERLET, T.CODTURMA,
    CAST(NULL AS nvarchar(max)) AS Instrutor
INTO #RM_ProfessoresPorTurma
FROM dbo.STURMA AS T;

DECLARE @StatusEstruturaInstrutor nvarchar(250) =
    N'Estrutura de professores não reconhecida ou sem permissão de metadados; enviar diagnóstico';
DECLARE @ExpressaoNome nvarchar(100) = NULL;
DECLARE @JoinPessoa nvarchar(500) = N'';
IF COL_LENGTH(N'dbo.STURMADISC', N'CODCOLIGADA') IS NOT NULL
    AND COL_LENGTH(N'dbo.STURMADISC', N'CODFILIAL') IS NOT NULL
    AND COL_LENGTH(N'dbo.STURMADISC', N'IDPERLET') IS NOT NULL
    AND COL_LENGTH(N'dbo.STURMADISC', N'CODTURMA') IS NOT NULL
    AND COL_LENGTH(N'dbo.STURMADISC', N'IDTURMADISC') IS NOT NULL
    AND COL_LENGTH(N'dbo.SPROFESSORTURMA', N'CODCOLIGADA') IS NOT NULL
    AND COL_LENGTH(N'dbo.SPROFESSORTURMA', N'IDTURMADISC') IS NOT NULL
    AND COL_LENGTH(N'dbo.SPROFESSORTURMA', N'CODPROF') IS NOT NULL
    AND COL_LENGTH(N'dbo.SPROFESSOR', N'CODCOLIGADA') IS NOT NULL
    AND COL_LENGTH(N'dbo.SPROFESSOR', N'CODPROF') IS NOT NULL
BEGIN
    IF COL_LENGTH(N'dbo.SPROFESSOR', N'CODPESSOA') IS NOT NULL
        AND COL_LENGTH(N'dbo.PPESSOA', N'CODIGO') IS NOT NULL
        AND COL_LENGTH(N'dbo.PPESSOA', N'NOME') IS NOT NULL
    BEGIN
        SET @ExpressaoNome = N'PE.NOME';
        SET @JoinPessoa = N' INNER JOIN dbo.PPESSOA AS PE ON PE.CODIGO = PR.CODPESSOA ';
    END
    ELSE IF COL_LENGTH(N'dbo.SPROFESSOR', N'NOME') IS NOT NULL
        SET @ExpressaoNome = N'PR.NOME';
END;

IF @ExpressaoNome IS NOT NULL
BEGIN
    -- SQL dinâmico evita compilar referências a colunas ausentes nas instalações RM.
    -- Identificadores fixos do código, sem entrada de usuário.
    DECLARE @SQLProfessores nvarchar(max) = N'
        INSERT INTO #RM_ProfessoresPorTurma
            (CODCOLIGADA, CODFILIAL, IDPERLET, CODTURMA, Instrutor)
        SELECT DISTINCT D.CODCOLIGADA, D.CODFILIAL, D.IDPERLET, D.CODTURMA,
            LTRIM(RTRIM(CONVERT(nvarchar(max), ' + @ExpressaoNome + N')))
        FROM dbo.STURMADISC AS D
        INNER JOIN dbo.SPROFESSORTURMA AS PT
            ON PT.CODCOLIGADA = D.CODCOLIGADA AND PT.IDTURMADISC = D.IDTURMADISC
        INNER JOIN dbo.SPROFESSOR AS PR
            ON PR.CODCOLIGADA = PT.CODCOLIGADA AND PR.CODPROF = PT.CODPROF '
        + @JoinPessoa + N'
        WHERE EXISTS (
            SELECT 1 FROM dbo.STURMA AS T
            WHERE T.CODCOLIGADA = D.CODCOLIGADA AND T.CODFILIAL = D.CODFILIAL
                AND T.IDPERLET = D.IDPERLET AND T.CODTURMA = D.CODTURMA
                AND T.DTFINAL >= @DataMinima
        );';
    EXEC sys.sp_executesql @SQLProfessores,
        N'@DataMinima date', @DataMinima = @FimAPartirDe;
    SET @StatusEstruturaInstrutor = N'Estrutura reconhecida; vínculos a validar no RM';
END;

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
    PROFESSORES.Instrutor AS [Instrutor], -- nomes distintos vinculados às disciplinas da turma
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
    T.TURMAENCERRADA AS [RM_Turma_Encerrada],
    CASE
        WHEN @ExpressaoNome IS NULL THEN @StatusEstruturaInstrutor
        WHEN PROFESSORES.Instrutor IS NULL THEN N'Sem nome de professor nos vínculos consultados'
        ELSE @StatusEstruturaInstrutor
    END AS [RM_Status_Instrutor]
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
OUTER APPLY (
    SELECT STUFF((
        SELECT N'; ' + NOMES.Instrutor
        FROM (
            SELECT DISTINCT I.Instrutor
            FROM #RM_ProfessoresPorTurma AS I
            WHERE I.CODCOLIGADA = T.CODCOLIGADA AND I.CODFILIAL = T.CODFILIAL
                AND I.IDPERLET = T.IDPERLET AND I.CODTURMA = T.CODTURMA
                AND I.Instrutor IS NOT NULL AND I.Instrutor <> N''
        ) AS NOMES
        ORDER BY NOMES.Instrutor
        FOR XML PATH(''), TYPE
    ).value('.', 'nvarchar(max)'), 1, 2, N'') AS Instrutor
) AS PROFESSORES
WHERE T.DTFINAL >= @FimAPartirDe
ORDER BY T.CODCOLIGADA, T.CODFILIAL, T.IDPERLET, T.CODTURMA;

-- A chave de turma e a cardinalidade dos joins são provisórias.
-- Resolver descrições/domínios e agregar matrículas e instrutores antes de adicioná-los.
-- Sem limite de linhas e sem filtro de início. Término no ano atual ou posterior; términos nulos ficam de fora.

DROP TABLE #RM_ProfessoresPorTurma;
