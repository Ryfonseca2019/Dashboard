# Power BI — Financiamento aplicado e pré-carga Niterói

Baixe **Planejamento_Turmas_SENAI_Financiamento_Aplicado_v19.zip**.

V19 — FINANCIAMENTO APLICADO POR REGRA APROVADA

CLASSIFICACAO 1/GRATUITO → Gratuidade; 2/NEGOCIO e 3/NEGOCIO PJ → Negócio.
A regra foi confirmada pelo usuário para a migração. O esquema recebido não prova formalmente o vínculo de configuração do campo com CLASSIFTUR; a associação é aplicada como regra de negócio autorizada, com validação atual dos rótulos de CLASSIFTUR (coligada 0, aplicação S) e das opções ativas do app.
Sem classificação, código desconhecido ou classificações conflitantes: sem financiamento e com status pendente. Não há valor padrão.
A extração anterior indica 4.932 Gratuidade e 2.026 Negócio, total 6.958 candidatas classificadas; 119 sem classificação. Essas contagens não são uma nova execução.

COMO USAR
Extraia em pasta nova e atualize o PBIP. Na página Financiamento e pré-carga Niterói:
- Tabela superior: DP_Financiamento_Confirmado com as três regras e IDs reais do app.
- Tabela inferior: Niteroi_PreCarga, com financiamento, pendências de matriz e campos obrigatórios vazios.
Exporte a inferior e envie para preparar o lote piloto. Não cole essa tabela de diagnóstico diretamente na lista.
O campo Financiamento é preenchido na Exportacao_App_Enriquecida e nas páginas Exportação | 54 campos e Colagem | sem metadados, que usam essa tabela.

Os campos técnicos ID_Financiamento_SharePoint e Status_Financiamento são de auditoria e não devem ser colados como colunas comuns. A ordem das 54/51 colunas anteriores foi preservada.
O check de obrigatórios usa o esquema do msapp recebido. Se você tornou pedagogo ou cálculo de evasão opcionais na lista, esse snapshot ainda os indicará; confirme as alterações reais antes da carga. Não foram removidas exigências na lista por esta entrega.
Unidade, planejamento, ano de referência, status Rascunho, Ativa e identificadores ainda devem ser conferidos na sua planilha: as decisões não equivalem a preenchimento automático de todos esses campos no PBIP atual. A visão não anuncia que o lote está pronto.
Turno continua pendente: o cadastro não corresponde com segurança ao horário efetivo de todas as turmas. Preservada carga horária do app e demais regras anteriores.
Nenhuma linha foi gravada no SharePoint ou RM. ZIP, referências e lógica de classificação verificados localmente; refresh e dados dependem do Desktop corporativo.
