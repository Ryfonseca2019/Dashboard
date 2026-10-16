-- Estrutura confirmada na exportação Campus.csv: SCAMPUS não possui coligada/filial.
-- Cadastro compartilhado; o filtro SENAI é aplicado nas turmas, não nesta tabela.
SELECT
    CAST(NULL AS int) AS RM_CODCOLIGADA,
    CAST(NULL AS int) AS RM_CODFILIAL_Cadastro,
    CONVERT(nvarchar(4000), C.CODCAMPUS) AS RM_Codigo_Campus,
    CAST(NULL AS nvarchar(4000)) AS RM_Nome_Campus,
    CONVERT(nvarchar(4000), C.DESCRICAO) AS RM_Descricao_Campus,
    CONVERT(int, C.TIPOCAMPUS) AS RM_Tipo_Campus,
    CONVERT(nvarchar(100), C.ATIVO) AS RM_Campus_Ativo,
    N'Cadastro sem coligada/filial; vínculo por CODCAMPUS' AS Escopo_Cadastro,
    N'dbo.SCAMPUS' AS Origem_Cadastro,
    N'Estrutura confirmada; validar descrição e vínculo com STURMA' AS Status_Cadastro_RM
FROM dbo.SCAMPUS AS C;
