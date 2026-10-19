SELECT N'Estrutura configuração' Origem,
CONVERT(nvarchar(4000),TABLE_SCHEMA+'.'+TABLE_NAME) Tabela,
CONVERT(nvarchar(4000),COLUMN_NAME) Campo,
CONVERT(nvarchar(4000),DATA_TYPE) Detalhe
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN ('GCAMPOSCOMPL','GCAMPOSCOMPLEMENTARES','GCOLUNAS','GCAMPOS')
 OR TABLE_NAME COLLATE Latin1_General_CI_AI LIKE '%CAMPO%COMPL%'
UNION ALL
SELECT N'Chave estrangeira',CONVERT(nvarchar(4000),OBJECT_SCHEMA_NAME(fkc.parent_object_id)+'.'+OBJECT_NAME(fkc.parent_object_id)),
CONVERT(nvarchar(4000),pc.name),CONVERT(nvarchar(4000),OBJECT_SCHEMA_NAME(fkc.referenced_object_id)+'.'+OBJECT_NAME(fkc.referenced_object_id)+'.'+rc.name)
FROM sys.foreign_key_columns fkc
JOIN sys.columns pc ON pc.object_id=fkc.parent_object_id AND pc.column_id=fkc.parent_column_id
JOIN sys.columns rc ON rc.object_id=fkc.referenced_object_id AND rc.column_id=fkc.referenced_column_id
WHERE OBJECT_NAME(fkc.parent_object_id)='STURMACOMPL' AND pc.name='TURNO'
UNION ALL
SELECT N'Rotulo do campo',CONVERT(nvarchar(4000),TABELA),CONVERT(nvarchar(4000),COLUNA),CONVERT(nvarchar(4000),DESCRICAO)
FROM dbo.GCAMPOS WHERE TABELA='STURMACOMPL' AND COLUNA='TURNO';