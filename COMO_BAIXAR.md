# Projeto Power BI — RM e SharePoint

Baixe **Planejamento_Turmas_RM_Com_Tabela_v2.zip** neste repositório, pelo botão de download do arquivo. Extraia o ZIP inteiro no Windows e abra **Análise exploratória.pbip** no Power BI Desktop atualizado.

A versão em arquivos está na pasta `Entrega_RM_SharePoint`.

Conecte-se à rede/VPN corporativa e execute **Atualizar**. A fonte SQL está configurada no projeto, mas sua conexão e a renderização ainda precisam ser validadas no Power BI Desktop. Não há senhas na entrega.

A página **RM → SharePoint | Amostra 200** contém os 54 campos de destino e identificadores técnicos. Apenas seis campos de destino têm expressões de origem identificadas no SQL fornecido; os outros 48 permanecem nulos até confirmação do mapeamento. A consulta usa ano 2026 e limite diagnóstico de 200 registros. Não é uma carga completa e não escreve no SharePoint.

Consulte `LEIA-ME - Tabela RM SharePoint.txt` dentro do ZIP para detalhes.

## Correção V2

Corrigida a propriedade `description:` inválida no TMDL da nova tabela. Baixe a V2 e extraia em uma pasta nova para evitar misturar versões. Abertura e atualização no Desktop continuam pendentes de validação.
