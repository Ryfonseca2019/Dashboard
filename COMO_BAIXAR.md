# Power BI — Catálogos e de/para do app

Baixe **Planejamento_Turmas_RM_Catalogos_App_v9.zip**.

V8 — CATÁLOGOS DO APP E DE/PARA DE MATRIZES

1. Extraia em pasta nova e abra o PBIP no Desktop atualizado.
2. Atualize usando acesso corporativo ao RM e Conta organizacional no SharePoint (mesmo site do app). A fonte Web das opções de escolha pode solicitar autenticação adicional. Nenhuma senha ou token foi salvo.
3. As tabelas APP_* consultam os cadastros reais do app, não exemplos nem uma lista inventada de opções. APP_Opcoes_Escolha lê as opções atuais de Choice via API; APP_Contrato_Campos registra o esquema do msapp recebido, que pode divergir da lista atual.
4. Confira as páginas Catálogos do app, Opções e contrato, De-para de matrizes e Exportação enriquecida.
5. DP_Matrizes_Candidatas sugere apenas nomes exatamente iguais. Nomes iguais não comprovam a mesma matriz: valide versão/currículo/carga/código antes de copiar a chave RM e o ID real para DP_Matrizes_Validadas, no Editor Avançado. Essa tabela começa vazia de propósito. Há detecção de chaves duplicadas.
6. Exportacao_App_Enriquecida usa somente matrizes aprovadas e copia código, nome, área, modalidade, mediação e carga diretamente de Cad_Matrizes, como o app. Captura as duas datas de snapshot e inclui Modalidade (campo adicional obrigatório). Se não houver de/para, os campos de matriz ficam vazios e o status indica a pendência. O status de matriz cruzada não significa migração completa.
7. DP_Turnos, DP_Financiamentos e DP_Campus_Polo expõem os IDs, rótulos e códigos SGE reais do app; são opções para validar, não associações RM já comprovadas. RM_Estrutura_Integracao deve ser exportada para confirmar as colunas RM de origem antes de automatizar esses campos.
8. Não foram derivados previsão de matrículas, pedagogo ou método de evasão do professor, das vagas ou de códigos sem comprovação. Esses dados dependem da origem/regra real. Parametros_Evasao_Unidade é carregado para validação das taxas por unidade/ano/modalidade; nenhuma taxa foi assumida.
9. Conferir Unidade e Planejamento por ID, cadastro de períodos, responsável Pessoa e todos os obrigatórios antes de colar. A V8 não preenche de forma automática Identificador_Temporario: use os identificadores já gerados e preservados na planilha do lote.

IMPORTANTE
Não é uma entrega pronta para migrar todas as linhas: faltam correspondências validadas RM ↔ app, autenticação e validação no Desktop. A consulta original de RM e seus professores foi preservada; o filtro segue término no ano atual em diante. Abertura, M, SQL, opções ao vivo e renderização não foram executados neste ambiente.
Lookup/Pessoa exigem entidades válidas; texto igual não garante que a colagem de grade resolverá o ID. Exportacao_App_Enriquecida inclui campos adicionais fora das 54 colunas; preparar uma exibição correspondente antes de colar. Não colar a coluna de status nem IDs técnicos como dados da lista.
Nenhuma linha de dados do app ou dos usuários foi publicada no GitHub; somente consultas, esquema e instruções. Preservar sua cópia local se já criou medidas/visuais.

V9 corrige a opção ApiVersion incompatível com o conector SharePoint 2.0, removendo-a das nove conexões de catálogos.
