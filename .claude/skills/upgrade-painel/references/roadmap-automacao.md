# Habilidades para o upgrade totalmente automático

Objetivo: você envia o arquivo de um painel Power BI e recebe (1) as melhorias priorizadas, (2) as novas visões
possíveis e, depois da sua escolha, (3) a nova versão validada e empacotada para abrir no Desktop.

Legenda: ✅ pronto · 🟡 pronto com ressalva · ⛔ fora do alcance desta sessão

| # | Habilidade | O que faz | Status | Onde está |
|---|---|---|---|---|
| 1 | Ingestão multi-formato | Pasta PBIP, `.pbip`, `.zip` (inclusive ZIP dentro de ZIP), `.pbit`, `.pbix` | ✅ (PBIX: modelo binário, campos inferidos dos visuais) | `analisar_painel.py` |
| 2 | Inventário completo | Páginas, visuais, posições, campos, cores, fontes, títulos, modelo, relacionamentos | ✅ | `analisar_painel.py` |
| 3 | Auditoria de design | ~40 verificações (Storytelling com Dados, Few, Nielsen, WCAG, IBCS) com evidência, princípio e comando | ✅ | `analisar_painel.py` |
| 4 | Revisão qualitativa | Grande ideia, títulos de ação, lógica horizontal, foco | ✅ feita pelo Claude seguindo a skill | `SKILL.md` |
| 5 | Novas visões | 11 padrões com campos reais e spec pronta (resumo, real × meta, tendência, recortes, qualidade + Pareto, drill-through, temas, dispersão, dica, mapa de calor, slopegraph) | ✅ | `analisar_painel.py` |
| 6 | Relatório priorizado | Índices, melhorias M, visões NV, "como aplicar" | ✅ | `relatorio.md` |
| 7 | Criação de páginas | 15 tipos de visual, drill-through e dica configurados, botões e navegador | ✅ | `pbir_tool.py criar` |
| 8 | Ajustes em visuais | Títulos, texto alternativo, ordem de leitura | ✅ | `pbir_tool.py ajustar` |
| 9 | Validação e regressão | Estrutura, campos, links de página, drill-through, tema, schema oficial, antes × depois | ✅ | `validar`, `validar_schema.py`, `comparar` |
| 10 | Empacotamento | ZIP `vNN+1` + LEIA_ME com changelog, bloqueia se a validação falhar | ✅ | `empacotar.py` |
| 11 | Reposicionar, alinhar, trocar tipo | `alinhar`, `layout`, `trocar-tipo` (pizza/gauge/linha → barras/cartão/linha) | ✅ | `pbir_tool.py` |
| 12 | Tema corporativo | Gera e registra tema (cinza + destaque + laranja de alerta, sem bordas/sombras) | ✅ | `pbir_tool.py tema` |
| 13 | Destaque e contexto | Cor por medida (top N, abaixo da meta, categoria), títulos dinâmicos, linha de meta, subtítulo, legenda/grade, ordenação | 🟡 medidas DAX e linha de meta conferidas no Desktop | `pbir_tool.py formatar` |
| 14 | Visuais avançados | Dispersão, real × meta, Pareto, slopegraph, mapa de calor | ✅ | `pbir_tool.py criar` |
| 15 | Navegação | Navegador de páginas, botões (página, drill-through, voltar, limpar filtros, URL), drill-through, dica de página, ordem/página inicial | 🟡 bookmarks continuam manuais | `pbir_tool.py` |
| 16 | Avaliação do visual renderizado | PDF → imagens por página; prints analisados pelo Claude | ✅ com PDF/prints · 🟡 exportação automática pelo Service escrita, não testada (exige workspace Premium/Fabric e token) | `paginas_pdf.py`, `exportar_service.py` |
| 17 | Leitura dos dados | Cardinalidade, nulos, atípicos e manchetes com números a partir de CSV/XLSX exportados | ✅ · ⛔ consulta direta ao modelo publicado (XMLA) depende de acesso ao tenant | `perfilar_dados.py` + `--dados` |
| 18 | Orquestração "um comando" | Arquivo → relatório → escolha → nova versão validada e empacotada | ✅ | `upgrade-painel/SKILL.md` |
| 19 | Apps Power Apps | Auditoria de UX de `.msapp` (acessibilidade, contraste, toque, delegação, erros, navegação, nomes, cores, desempenho) | ✅ análise · ⛔ edição automática do app (feita no Power Apps Studio) | `analisar_app.py` |

## Limites que continuam

- **Power BI Desktop não roda aqui.** Tudo é validado estaticamente e contra o schema oficial; a renderização e as
  medidas DAX novas se confirmam ao abrir no Desktop. Os comandos avisam com `NOTA` o que conferir.
- **Bookmarks** não são gerados: o estado que eles capturam (filtros, visuais visíveis, seleção) é frágil para
  montar sem o Desktop.
- **Service/Fabric** (prints automáticos, leitura direta do modelo): o script está pronto, mas precisa de
  workspace com capacidade Premium/Fabric, token e liberação do host `api.powerbi.com` no ambiente.
- **Power Apps:** a auditoria é automática; as correções são aplicadas no Studio (o `.msapp` não é editado aqui).

## O que enviar para a análise ficar completa

- O painel em **PBIP (ZIP da pasta)** ou **PBIT**. O PBIX funciona, mas sem o modelo.
- **PDF** do relatório (Arquivo › Exportar › PDF) ou prints.
- **CSVs exportados** dos visuais principais (Mais opções › Exportar dados), para manchetes com números.
- Uma frase sobre **quem usa** e **que decisão toma** (L1).
