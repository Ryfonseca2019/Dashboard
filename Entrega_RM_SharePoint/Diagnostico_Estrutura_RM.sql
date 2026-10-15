-- Executar no banco CorporeRM com acesso autorizado.
-- Somente leitura de estrutura: não retorna alunos, credenciais ou dados de negócio.
-- Não pressupõe que os cadastros adicionais existam nesta instalação.
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN (
    'STURMA', 'SPLETIVO', 'GFILIAL', 'SHABILITACAOFILIAL', 'SCURSO',
    'SMATRICPL', 'STURMADISC', 'SPROFESSOR', 'SPROFESSORTURMA',
    'SGRADE', 'STURNO', 'SCAMPUS', 'SPREDIO', 'SSALA',
    'SMODALIDADECURSO', 'SSTATUS', 'STURMACOMPL', 'SCURSOCOMPL',
    'GCCUSTO'
)
ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION;
