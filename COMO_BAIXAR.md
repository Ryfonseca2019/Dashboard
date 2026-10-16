# Power BI — Campus RM com estrutura confirmada

Baixe **Planejamento_Turmas_SENAI_Campus_Corrigido_v13.zip**.

V13 — CAMPUS RM: ESTRUTURA REAL CONFIRMADA

A exportação Campus.csv confirmou que dbo.SCAMPUS tem CODCAMPUS, DESCRICAO, TIPOCAMPUS e ATIVO, mas não tem CODCOLIGADA nem CODFILIAL. A condição da V12 foi removida: ela exigia uma coluna inexistente.
Campus_Cadastro_RM agora consulta diretamente esses campos. Coligada e filial desse cadastro são nulas por não existirem; isso não significa turma sem unidade. A seleção de turmas continua restrita à coligada 3 (SENAI), com término no ano atual em diante.
O cruzamento usa CODCAMPUS textual e mantém contagem de candidatos. Se o cadastro tiver códigos repetidos, o resultado será marcado como ambíguo sem multiplicar as linhas do resumo. Zeros à esquerda não são removidos. A equivalência com as categorias do app continua pendente de validação das descrições.
RM_Tipo_Campus e RM_Campus_Ativo são valores brutos, sem assumir a tradução de seus códigos. O campo descritivo desta instalação é RM_Descricao_Campus; RM_Nome_Campus permanece nulo porque SCAMPUS não tem NOME.

PARA EXPORTAR
Extraia em pasta nova, abra o PBIP e clique em Atualizar. Na página Campus SENAI - descrições, envie a tabela superior (Campus_SENAI_Validar) e a inferior esquerda (Campus_Cadastro_RM). A tabela inferior direita contém as opções do app e não precisa ser reenviada se o cadastro não mudou.

Mantidas matrículas previstas iguais às vagas, pedagogo vazio e demais regras anteriores. Não há preenchimento automático de Campus_Polo nem alteração do cadastro SharePoint nesta versão: a validação das descrições permitirá fazê-lo corretamente.
Estrutura dos arquivos, campos dos visuais, SQL/M e integridade do ZIP foram conferidos. Execução no RM e renderização precisam ser confirmadas no Desktop.
