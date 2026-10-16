-- Resumo independente de outras consultas Power Query.
-- Somente leitura; mesma seleção SENAI e término previsto no ano atual em diante.
WITH Turmas AS (
    SELECT DISTINCT CODCOLIGADA,CODFILIAL,IDPERLET,CODTURMA
    FROM dbo.STURMA
    WHERE CODCOLIGADA=3 AND DTFINAL>=DATEFROMPARTS(YEAR(GETDATE()),1,1)
), Classificacoes AS (
    SELECT DISTINCT T.CODCOLIGADA,T.CODFILIAL,T.IDPERLET,T.CODTURMA,
        NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(4000),C.CLASSIFICACAO))),N'') AS Codigo
    FROM Turmas T
    LEFT JOIN dbo.STURMACOMPL C ON C.CODCOLIGADA=T.CODCOLIGADA
        AND C.CODFILIAL=T.CODFILIAL AND C.IDPERLET=T.IDPERLET AND C.CODTURMA=T.CODTURMA
), Resumo AS (
    SELECT Codigo,COUNT_BIG(*) AS Quantidade_Turmas
    FROM Classificacoes GROUP BY Codigo
), Dominio AS (
    SELECT CONVERT(nvarchar(4000),CODCLIENTE) AS Codigo,COUNT(*) AS N,
        CASE WHEN COUNT(*)=1 THEN MAX(CONVERT(nvarchar(4000),DESCRICAO)) END Descricao
    FROM dbo.GCONSIST
    WHERE CODCOLIGADA=0 AND APLICACAO='S' AND CODTABELA='CLASSIFTUR'
    GROUP BY CONVERT(nvarchar(4000),CODCLIENTE)
)
SELECT R.Codigo AS RM_CLASSIFICACAO,R.Quantidade_Turmas,
    COALESCE(D.N,0) AS Ocorrencias_Dominio,D.Descricao AS Descricao_CLASSIFTUR,
    CASE WHEN D.N=1 THEN N'S' END AS Aplicacao_Dominio,
    CASE R.Codigo WHEN N'1' THEN N'Gratuidade' WHEN N'2' THEN N'Negócio' WHEN N'3' THEN N'Negócio' END AS Financiamento_Proposto,
    CASE WHEN R.Codigo IS NULL THEN N'Sem classificação na turma'
        WHEN R.Codigo NOT IN (N'1',N'2',N'3') THEN N'Classificação sem regra aprovada'
        WHEN COALESCE(D.N,0)<>1 THEN N'Domínio ausente ou ambíguo'
        WHEN (R.Codigo=N'1' AND D.Descricao<>N'GRATUITO')
          OR (R.Codigo=N'2' AND D.Descricao<>N'NEGOCIO')
          OR (R.Codigo=N'3' AND D.Descricao<>N'NEGOCIO PJ') THEN N'Descrição do domínio mudou; revisar'
        ELSE N'Regra de migração confirmada; opção atual do app validada no de/para de produção'
    END AS Status_Validacao
FROM Resumo R LEFT JOIN Dominio D ON D.Codigo=R.Codigo;
