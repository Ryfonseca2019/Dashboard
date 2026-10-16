# Power BI — Término previsto no ano atual em diante

Baixe **Planejamento_Turmas_RM_Fim_Ano_Atual_v5.zip**.

PROJETO POWER BI — V5 — TÉRMINO NO ANO ATUAL EM DIANTE

Extraia o ZIP em uma pasta nova, abra Análise exploratória.pbip no Power BI Desktop, conecte-se à rede corporativa e execute Atualizar.
Use a página RM → SharePoint | Fim ano atual+ e a consulta RM_Integracao_SharePoint.

REGRA
STURMA.DTFINAL >= DATEFROMPARTS(YEAR(GETDATE()), 1, 1).
Inclui turmas com término previsto em qualquer dia do ano atual ou dos próximos anos, independentemente da data de início. Não significa somente as turmas que terminam a partir de hoje.
O ano é determinado pela data do servidor SQL Server RM no momento da atualização. Em 2026, inclui término a partir de 01/01/2026; em 2027, a partir de 01/01/2027. Como o modelo é Import, deve ser atualizado para refletir a mudança de ano.
Não há limite de linhas. Términos nulos ficam de fora. Datas de início não são filtradas.
Mantido LEFT JOIN do período letivo para não excluir turmas sem correspondência nesse cadastro. Unicidade e demais vínculos precisam ser confirmados no banco.

LIMITAÇÕES
Seis campos de destino têm origem identificada e 48 permanecem nulos até completar o mapeamento. Não há escrita no SharePoint.
As consultas originais foram preservadas, com suas regras antigas; use RM_Integracao_SharePoint para a regra nova.
A fonte está configurada, mas conexão, resultados, DAX e renderização ainda precisam de validação no Power BI Desktop com acesso ao RM. Este ZIP não inclui caches .pbi nem alterações que você tenha feito apenas em sua cópia local.
