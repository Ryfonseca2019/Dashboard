# Power BI — Campus/Polo preenchido pelo de/para confirmado

Baixe **Planejamento_Turmas_SENAI_Campus_Preenchido_v14.zip**.

V14 — CAMPUS/POLO CONFIRMADO E PREENCHIDO NA EXPORTAÇÃO

Correspondência validada nas exportações recebidas:
RM 1 → Matriz da Escola - Senai → ID SharePoint 3.
RM 2 → Unidades Móveis - Senai → ID SharePoint 4.
RM 3 → Agência / Extensão - Senai → ID SharePoint 1.
RM 4 → Unidades Remotas - Senai → ID SharePoint 5.
RM 5 → Ambiente da Empresa - Senai → ID SharePoint 2.

A tabela DP_Campus_Confirmado valida a descrição e atividade atuais no RM e no app em cada atualização. O ID real vem do catálogo SharePoint atualizado; a coluna Codigo_SGE vazia nesse catálogo não impede a associação já confirmada por descrição e código RM. Nenhuma alteração no cadastro SharePoint foi realizada.
RM_Integracao_SharePoint agora preenche Campus_Polo usando esse de/para. As páginas Colagem | sem metadados, Exportação | 54 campos e Exportação enriquecida herdam o resultado. Foram adicionados ID_Campus_SharePoint e Status_Campus no modelo para diagnóstico, sem alterar a ordem das 54 colunas do visual de exportação.
Códigos sem correspondência, vazios, inativos, duplicados ou com descrição alterada ficam sem preenchimento e com status de pendência; não são convertidos em Matriz da Escola por padrão.

A exportação recebida contém 7.077 turmas SENAI: 7.031 com código e descrição correspondentes, 46 sem código. Niterói possui 510 turmas e todas têm correspondência. Esses números descrevem os arquivos recebidos, não uma nova execução desta versão.

COMO USAR
Extraia em pasta nova, abra o PBIP e clique em Atualizar. A página De-para Campus confirmado mostra as cinco correspondências e o status atual. Para exportar, use Colagem | sem metadados ou a saída enriquecida conforme o layout e os demais campos já validados.
Outros campos obrigatórios e de/para ainda pendentes não são resolvidos por esta versão. Não é confirmação de carga completa. Preserve os identificadores do lote e os dados ajustados manualmente em sua planilha.
Somente SENAI, término no ano atual em diante, matrículas previstas iguais às vagas e pedagogo vazio permanecem mantidos. Os demais ajustes de negócio discutidos ainda devem ser conferidos separadamente.
Conexão, SQL, M e renderização da V14 precisam ser executados no Desktop corporativo. Estrutura, referências, correspondências dos arquivos e ZIP foram verificados.
