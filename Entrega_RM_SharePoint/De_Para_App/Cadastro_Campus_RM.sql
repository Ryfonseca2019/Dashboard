SET NOCOUNT ON;
-- Somente leitura. Coligada 3 = SENAI conforme exportações recebidas.
-- Detecta colunas antes de compilar a consulta ao cadastro.
IF COL_LENGTH(N'dbo.SCAMPUS', N'CODCOLIGADA') IS NOT NULL
    AND COL_LENGTH(N'dbo.SCAMPUS', N'CODCAMPUS') IS NOT NULL
    AND (COL_LENGTH(N'dbo.SCAMPUS', N'NOME') IS NOT NULL
         OR COL_LENGTH(N'dbo.SCAMPUS', N'DESCRICAO') IS NOT NULL)
BEGIN
    DECLARE @Filial nvarchar(150) = N'CAST(NULL AS int)';
    DECLARE @Nome nvarchar(150) = N'CAST(NULL AS nvarchar(4000))';
    DECLARE @Descricao nvarchar(150) = N'CAST(NULL AS nvarchar(4000))';
    DECLARE @Escopo nvarchar(100) = N'Coligada e código; sem coluna CODFILIAL';
    IF COL_LENGTH(N'dbo.SCAMPUS', N'CODFILIAL') IS NOT NULL
    BEGIN
        SET @Filial = N'CONVERT(int, C.CODFILIAL)';
        SET @Escopo = N'Coligada, filial e código';
    END;
    IF COL_LENGTH(N'dbo.SCAMPUS', N'NOME') IS NOT NULL
        SET @Nome = N'CONVERT(nvarchar(4000), C.NOME)';
    IF COL_LENGTH(N'dbo.SCAMPUS', N'DESCRICAO') IS NOT NULL
        SET @Descricao = N'CONVERT(nvarchar(4000), C.DESCRICAO)';
    DECLARE @SQL nvarchar(max) =
        N'SELECT CONVERT(int,C.CODCOLIGADA) AS RM_CODCOLIGADA, '
        + @Filial + N' AS RM_CODFILIAL_Cadastro,
        CONVERT(nvarchar(4000),C.CODCAMPUS) AS RM_Codigo_Campus, '
        + @Nome + N' AS RM_Nome_Campus, '
        + @Descricao + N' AS RM_Descricao_Campus,
        @Escopo AS Escopo_Cadastro,
        N''dbo.SCAMPUS'' AS Origem_Cadastro,
        N''Cadastro encontrado; validar vínculo e significado'' AS Status_Cadastro_RM
        FROM dbo.SCAMPUS AS C WHERE C.CODCOLIGADA = 3;';
    EXEC sys.sp_executesql @SQL, N'@Escopo nvarchar(100)', @Escopo=@Escopo;
END
ELSE
BEGIN
    SELECT CONVERT(int,3) AS RM_CODCOLIGADA,
        CAST(NULL AS int) AS RM_CODFILIAL_Cadastro,
        CAST(NULL AS nvarchar(4000)) AS RM_Codigo_Campus,
        CAST(NULL AS nvarchar(4000)) AS RM_Nome_Campus,
        CAST(NULL AS nvarchar(4000)) AS RM_Descricao_Campus,
        N'Não identificado' AS Escopo_Cadastro,
        N'dbo.SCAMPUS não validado' AS Origem_Cadastro,
        N'Colunas/cadastro não encontrados ou metadados sem permissão; exportar Campus_Estrutura_RM' AS Status_Cadastro_RM;
END;
