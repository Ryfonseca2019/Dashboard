SET NOCOUNT ON;
IF COL_LENGTH(N'dbo.GCONSIST',N'CODTABELA') IS NOT NULL
 AND COL_LENGTH(N'dbo.GCONSIST',N'CODCLIENTE') IS NOT NULL
 AND COL_LENGTH(N'dbo.GCONSIST',N'DESCRICAO') IS NOT NULL
BEGIN
 DECLARE @ExprCol nvarchar(100)=N'CAST(NULL AS int)';
 DECLARE @FiltroCol nvarchar(200)=N'';
 DECLARE @MesmaCol nvarchar(200)=N'';
 IF COL_LENGTH(N'dbo.GCONSIST',N'CODCOLIGADA') IS NOT NULL
 BEGIN
  SET @ExprCol=N'CONVERT(int,C.CODCOLIGADA)';
  SET @FiltroCol=N' AND C.CODCOLIGADA IN (0,3) ';
  SET @MesmaCol=N' AND D.CODCOLIGADA=C.CODCOLIGADA ';
 END;
 DECLARE @Sql nvarchar(max)=N'
 SELECT '+@ExprCol+N' AS CODCOLIGADA,
  CONVERT(nvarchar(4000),C.CODTABELA) AS Codigo_Tabela,
  CONVERT(nvarchar(4000),C.CODCLIENTE) AS Codigo_Valor,
  CONVERT(nvarchar(4000),C.DESCRICAO) AS Descricao_Valor,
  N''Candidato por texto: validar vínculo com campo complementar'' AS Status_Dominio
 FROM dbo.GCONSIST C
 WHERE EXISTS (
  SELECT 1 FROM dbo.GCONSIST D
  WHERE D.CODTABELA=C.CODTABELA '+@MesmaCol+N'
  AND (
    UPPER(CONVERT(nvarchar(4000),D.CODTABELA)) LIKE N''%TURNO%''
    OR UPPER(CONVERT(nvarchar(4000),D.CODTABELA)) LIKE N''%CLASSIF%''
    OR UPPER(CONVERT(nvarchar(4000),D.CODTABELA)) LIKE N''%FINANC%''
    OR UPPER(CONVERT(nvarchar(4000),D.DESCRICAO)) IN
       (N''MANHÃ'',N''MANHA'',N''TARDE'',N''NOITE'',N''INTEGRAL'',N''PERSONALIZADO'',N''GRATUIDADE'',N''NEGÓCIO'',N''NEGOCIO'')
    OR UPPER(CONVERT(nvarchar(4000),D.DESCRICAO)) LIKE N''%GRATUIDADE%''
  )
 ) '+@FiltroCol+N';';
 EXEC sys.sp_executesql @Sql;
END
ELSE
 SELECT CAST(NULL AS int) AS CODCOLIGADA,
  CAST(NULL AS nvarchar(4000)) AS Codigo_Tabela,
  CAST(NULL AS nvarchar(4000)) AS Codigo_Valor,
  CAST(NULL AS nvarchar(4000)) AS Descricao_Valor,
  N'GCONSIST/colunas não reconhecidas ou sem metadados; exportar RM_Dominios_Estrutura' AS Status_Dominio;
