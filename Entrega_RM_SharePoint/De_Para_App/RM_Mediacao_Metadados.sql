SELECT N'Coluna' Origem, CONVERT(nvarchar(4000),TABLE_SCHEMA+'.'+TABLE_NAME) Tabela,
CONVERT(nvarchar(4000),COLUMN_NAME) Campo,CONVERT(nvarchar(4000),DATA_TYPE) Detalhe
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME COLLATE Latin1_General_CI_AI LIKE '%MEDIAC%'
 OR COLUMN_NAME COLLATE Latin1_General_CI_AI LIKE '%MEDIAC%'
UNION ALL
SELECT N'Rotulo GCAMPOS',CONVERT(nvarchar(4000),TABELA),CONVERT(nvarchar(4000),COLUNA),CONVERT(nvarchar(4000),DESCRICAO)
FROM dbo.GCAMPOS WHERE CONVERT(nvarchar(4000),COLUNA) COLLATE Latin1_General_CI_AI LIKE '%MEDIAC%'
 OR CONVERT(nvarchar(4000),DESCRICAO) COLLATE Latin1_General_CI_AI LIKE '%MEDIAC%'
UNION ALL
SELECT N'Restricao CHECK',CONVERT(nvarchar(4000),OBJECT_SCHEMA_NAME(parent_object_id)+'.'+OBJECT_NAME(parent_object_id)),CONVERT(nvarchar(4000),name),CONVERT(nvarchar(4000),definition)
FROM sys.check_constraints WHERE definition COLLATE Latin1_General_CI_AI LIKE '%MEDIAC%'
UNION ALL
SELECT N'Descricao SQL',CONVERT(nvarchar(4000),OBJECT_SCHEMA_NAME(c.object_id)+'.'+OBJECT_NAME(c.object_id)),CONVERT(nvarchar(4000),c.name),CONVERT(nvarchar(4000),ep.value)
FROM sys.columns c JOIN sys.extended_properties ep ON ep.class=1 AND ep.major_id=c.object_id AND ep.minor_id=c.column_id
WHERE c.name COLLATE Latin1_General_CI_AI LIKE '%MEDIAC%';