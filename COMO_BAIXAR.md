# Power BI — Comparação de Campus/Polo

Baixe **Planejamento_Turmas_RM_Comparacao_Campus_v11.zip**.

V11 — VISÃO PARA COMPARAR CAMPUS/POLO

Extraia o ZIP em uma pasta nova, abra Análise exploratória.pbip no Desktop e execute Atualizar com acesso corporativo ao RM e conta organizacional do SharePoint.
Abra a página Comparar Campus-Polo, selecionada ao abrir.

Há três visuais independentes:
- Superior esquerdo, Campus_RM_Exportar: coligada, filial, unidade, código de campus, quantidade de turmas distintas e quantidade de linhas da fonte.
- Superior direito, Campus_App_Exportar: ID real do cadastro, código SGE, rótulo do app, Ativa, contagem de ocorrências do código e status de cadastro. Inclui opções inativas e sem código para diagnóstico.
- Inferior, Campus_Comparacao: candidatos por igualdade do código e diagnóstico. Códigos iguais não comprovam equivalência de negócio; este visual não aprova nem preenche o de/para automaticamente.

Em cada visual, clique em ... > Exportar dados e envie os arquivos. Os dois superiores são suficientes; se possível, envie também o inferior.
Os arquivos não incluem nomes de professores ou alunos. Não acrescente dados pessoais.
RM agrupa as turmas da seleção atual: término previsto no ano corrente ou posterior, sem filtro de início. Não usa apenas Niterói: identifica cada unidade encontrada na fonte. Turmas sem código de campus são incluídas em grupo vazio.
O código é comparado como texto, retirando apenas espaços externos; zeros à esquerda são preservados. Não há associação automática por nome.
As tabelas superiores não dependem da comparação nem do de/para de matrizes. Contudo, a atualização do projeto completo continua dependendo das demais fontes e credenciais.

Nenhuma opção foi inventada e nenhuma correspondência foi aprovada. As regras SQL e os dados de cadastro não foram alterados. As decisões anteriores de matrículas previstas iguais às vagas e pedagogo em branco foram preservadas.
A estrutura, campos de visuais e ZIP foram verificados; conexão RM/SharePoint, Power Query e renderização precisam ser validados no seu Desktop.
