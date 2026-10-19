SELECT CONVERT(nvarchar(4000),QUOTENAME(OBJECT_SCHEMA_NAME(m.object_id))+'.'+QUOTENAME(OBJECT_NAME(m.object_id))) Objeto,
CONVERT(nvarchar(100),o.type_desc) Tipo_Objeto,
CONVERT(nvarchar(4000),SUBSTRING(m.definition,CASE WHEN CHARINDEX('TIPOMEDIACAO',UPPER(m.definition))>1000 THEN CHARINDEX('TIPOMEDIACAO',UPPER(m.definition))-1000 ELSE 1 END,4000)) Trecho_Definicao
FROM sys.sql_modules m JOIN sys.objects o ON o.object_id=m.object_id
WHERE m.definition COLLATE Latin1_General_CI_AI LIKE '%TIPOMEDIACAO%'
ORDER BY Objeto;