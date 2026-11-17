# AutoView 3.1.5 — revisão de segurança preliminar

## Estado da distribuição
O Edge/antivírus bloqueou AutoView_3.1.5_correcao_abas.zip com “Vírus detectado”.
O Histórico de Proteção mostrou alertas graves e correção incompleta. O usuário não possui acesso administrativo aos detalhes.
O nome da detecção, o mecanismo e o arquivo interno sinalizado são desconhecidos. Não foi possível confirmar se os itens vistos no Histórico de Proteção correspondem ao ZIP.
**Não há evidência suficiente para declarar falso positivo nem para identificar a assinatura responsável.**
Os testes funcionais anteriores não foram uma análise antivírus. Não se recomenda permitir o arquivo ou desativar a proteção.

## Escopo e evidências
Foram obtidos do GitHub os dois arquivos exatos, usando leitura base64, e inspecionados em memória:
- 3.1.4 corrigida: blob 056c891be1b308fbda3866f21f0954ceba8e39cc, 14 entradas.
- 3.1.5: blob bec3a9530e8f1b6d3f74b4cdfc216238b6708d5e, 16 entradas.
Cada entrada teve tamanho e CRC32 verificados. Isso valida a extração, não a segurança.
Comparação: 9 arquivos idênticos, 5 modificados e 2 documentos adicionados.
Os quatro ícones, selector.js, screen.js, screen.html, popup.js e style.css são idênticos entre os pacotes.
Alterações da 3.1.5: background.js, options.js, options.html, manifest.json, popup.html; adicionados LEIA-ME.txt e VALIDACAO.json.
O pacote não contém executáveis Windows, instaladores, PowerShell, bibliotecas externas ou o script PowerShell fornecido anteriormente no chat.
Os arquivos JavaScript da extensão não foram executados nesta revisão; as verificações dinâmicas se restringiram às novas funções de validação.

## Achados estáticos
- Não foram encontrados eval, Function, importação dinâmica de scripts, scripts codificados/descompactados ou download de código nos JavaScript da extensão.
- Não foram encontrados fetch, XMLHttpRequest, WebSocket ou sendBeacon para remessa de dados a um servidor de coleta.
- Não foram encontrados acessos a cookies, histórico, credenciais ou leitura da área de transferência.
- A navegação para URLs de dashboard cadastradas é parte do funcionamento e realiza conexões normais do navegador.
- “scripting” é declarada, mas não é utilizada pela versão 3.1.5.
- O acesso a http://*/* e https://*/* e a injeção do seletor nesses sites já existiam na versão anterior. São amplos e merecem redução, mas não é possível atribuir o alerta a eles.
- Mensagens de configuração e controle não validavam uniformemente identidade da extensão, página de origem e frame.
- A importação aceitava valores de imagem posteriormente interpolados em HTML sem validação/escape uniforme.
Esses achados são oportunidades reais de endurecimento, NÃO evidência de que originaram a detecção.

## Proposta preparada (rascunho 3.1.6, NÃO HOMOLOGADO)
- Tornar explícita a CSP das páginas internas: scripts somente do próprio pacote, objetos bloqueados e sem elemento base.
- Remover scripting, sem uso nesta base, e a declaração windows, desnecessária para as APIs utilizadas. Permanecem tabs, alarms, storage e system.display.
- Restringir comandos às páginas internas que realmente os utilizam ou ao content script do frame principal da janela vinculada ao Monitor 1.
- Validar quatro perfis únicos, IDs de itens únicos, intervalos, URLs HTTP(S) sem credenciais embutidas e imagens locais PNG/JPEG/WebP em data URI.
- Escapar atributos de imagem e rejeitar imagens remotas, SVG/HTML ou conteúdo de atributo injetado.
- Rejeitar importação inválida em vez de modificá-la silenciosamente. Os testes verificam preservação de configurações válidas.
Os direitos de host continuam amplos neste rascunho para não quebrar dashboards de domínios ainda não inventariados. A redução exige listar os domínios usados e validar a forma de concessão de acesso.

## Testes e limitações
22 verificações isoladas passaram (TESTES-ISOLADOS.json).
As funções de validação foram executadas em um isolate JavaScript com metadados de remetente simulados.
A verificação usa um substituto simples para o parser de URL existente; não é um teste do URL nativo do Edge. O parser nativo anterior não foi alterado.
Os scripts da proposta foram analisados sintaticamente, sem executar a extensão inteira.
O ambiente de execução do projeto falhou; não foi possível executar Node/Playwright, regressão completa, teste MV3 ou scanner antivírus.
Este diretório é para revisão de código. **Não é uma atualização recomendada para instalar nem uma garantia de ausência de malware. Não há ZIP novo liberado.**
A proteção contra exibir dashboards em carregamento continua pendente e não foi incorporada a este rascunho.

## Critérios para liberar
1. Recuperar um ambiente funcional e executar regressão de configuração, mensagens, backup/importação, menu, rotação e prevenção de duplicações.
2. Obter por meio da TI o nome da detecção e o item interno afetado; verificar também os registros de correção incompleta.
3. Examinar o artefato de distribuição com o mecanismo que o bloqueou e ferramentas de análise autorizadas. Se houver falso positivo confirmado, encaminhar ao fornecedor para revisão.
4. Fazer revisão do código e empacotamento reproduzível, com checksum da distribuição e inventário de arquivos.
5. Manter o bloqueio da versão sinalizada até esclarecimento. Não mudar nomes, extensões ou empacotamento para tentar escapar da detecção.

## Ícones
Os quatro PNGs tiveram assinatura, limites dos chunks e CRCs verificados. Nenhum possui bytes após IEND. Isso é verificação estrutural de imagem, não análise antivírus.
