# Habilidades para o upgrade totalmente automático

Objetivo: você envia o arquivo de um painel Power BI e recebe (1) as melhorias priorizadas, (2) as novas visões
possíveis e, depois da sua escolha, (3) a nova versão pronta para abrir no Desktop.

Legenda: ✅ pronto · 🟡 parcial · 🔜 a desenvolver

| # | Habilidade | O que faz | Status | Onde está |
|---|---|---|---|---|
| 1 | Ingestão multi-formato | Lê pasta PBIP, `.pbip`, `.zip` (inclusive ZIP dentro de ZIP), `.pbit` e `.pbix` | ✅ (no PBIX o modelo é binário: campos inferidos dos visuais) | `upgrade-painel/scripts/analisar_painel.py` |
| 2 | Inventário completo | Páginas, visuais, posições, campos, cores, fontes, títulos, tabelas, medidas, relacionamentos | ✅ | idem (`inventario.json`) |
| 3 | Auditoria de design | ~35 verificações de Storytelling com Dados, Few, Nielsen, WCAG e IBCS, com evidência e recomendação | ✅ heurísticas estáticas | idem (`analise.json`, `relatorio.md`) |
| 4 | Revisão qualitativa | Títulos de ação, grande ideia, lógica horizontal das páginas, adequação ao público | ✅ feita pelo Claude seguindo a skill | `upgrade-painel/SKILL.md` |
| 5 | Gerador de novas visões | 9 padrões a partir do modelo, com campos reais e layout pronto | ✅ | `analisar_painel.py` (`specs/`) |
| 6 | Relatório priorizado | Índices por dimensão, melhorias (M) e visões (NV) numeradas para escolha | ✅ | idem |
| 7 | Criação de páginas | Gera páginas e 9 tipos de visual em PBIR | ✅ | `pbir-paginas-visuais/scripts/pbir_tool.py criar` |
| 8 | Ajustes em visuais existentes | Títulos, texto alternativo, ordem de leitura/tabulação | ✅ | `pbir_tool.py ajustar` |
| 9 | Validação e regressão | Estrutura, campos, schema oficial e comparação antes × depois | ✅ | `pbir_tool.py validar`, `validar_schema.py`, `analisar_painel.py comparar` |
| 10 | Empacotamento da entrega | ZIP `vNN+1` + `LEIA_ME` no padrão do repositório | 🟡 por instruções | `upgrade-painel/SKILL.md` |
| 11 | Reposicionar e alinhar | Encaixar visuais existentes na grade, mover KPIs para o topo, trocar tipo de visual (pizza → barras) | 🔜 | estender `pbir_tool.py` |
| 12 | Tema corporativo | Gerar e aplicar tema JSON (cinza + destaque + status, fontes, sem bordas) | 🔜 | nova skill `tema-painel` |
| 13 | Destaque e contexto | Formatação condicional (cinza + cor de destaque), linhas de meta/média, rótulos diretos, títulos dinâmicos em DAX | 🔜 | `pbir_tool.py` + skill de DAX |
| 14 | Visuais avançados | Dispersão, bullet (real × meta), slopegraph, mapa de calor, Pareto | 🔜 | estender `pbir_tool.py criar` |
| 15 | Navegação | Navegador de páginas, botões, bookmarks, drill-through e tooltip configurados no JSON | 🔜 | estender `pbir_tool.py` |
| 16 | Avaliação do visual renderizado | Analisar prints de cada página (cores reais, legibilidade, dados vazios) | 🟡 hoje com prints/PDF enviados por você; 🔜 automático via exportação do Power BI Service/Fabric (requer workspace e credencial) | — |
| 17 | Leitura dos dados | Cardinalidade, nulos, atípicos e números reais para escolher visuais e escrever manchetes com valores | 🔜 requer acesso ao modelo publicado (XMLA/Fabric) ou CSVs exportados | — |
| 18 | Orquestração "um comando" | Arquivo recebido → relatório → escolha → nova versão validada | ✅ | `upgrade-painel/SKILL.md` |
| 19 | Apps Power Apps (`.msapp`) | Mesma auditoria para os apps | 🔜 fora do escopo atual | nova skill |

## Ordem sugerida para desenvolver

1. **#11 Reposicionar e alinhar** e **#14 visuais avançados**: aumentam o que sai pronto sem abrir o Desktop.
2. **#12 Tema corporativo**: resolve cor, fonte e borda de uma vez em todos os painéis.
3. **#13 Destaque e contexto**: é o coração do Storytelling com Dados (foco com cor e títulos dinâmicos).
4. **#10 Empacotamento em script** e **#15 navegação**.
5. **#16/#17**, quando houver acesso ao Power BI Service/Fabric a partir desta sessão.

## O que você pode enviar para a análise ficar mais completa

- O painel em **PBIP (ZIP da pasta)** ou **PBIT**. O PBIX funciona, mas sem o modelo.
- **Prints ou PDF** das páginas (Arquivo › Exportar › PDF), para avaliar cores e legibilidade reais.
- Uma frase sobre **quem usa** e **que decisão toma**: é o ponto de partida do livro (L1).
