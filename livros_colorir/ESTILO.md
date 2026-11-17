# Guia de estilo dos livros

Estas regras valem para todo livro da coleção. As que dá para medir estão em
`colorbook/estilo.py`, e o auditor (`python -m colorbook auditar`) confere cada página
contra elas. As outras dependem de revisão humana.

## Regras medidas pelo auditor

| Regra | 2 a 5 anos | 5 a 10 anos | Por quê |
|---|---|---|---|
| Traço mínimo | 1,5 pt (0,5 mm) | 1,0 pt (0,35 mm) | Traço fino some no papel e a criança não enxerga a borda |
| Menor área para pintar | 0,8 cm² | 0,2 cm² | Áreas menores frustram: a criança não consegue pintar sem sair |
| Áreas por página | 4 a 45 | 8 a 220 | Poucas deixam a página pobre; muitas cansam |
| Ocupação da área útil | ≥ 60% | ≥ 65% | Página com metade em branco parece "vazia" e gera reclamação |
| Páginas parecidas | nenhuma acima de 85% | igual | Repetição é a reclamação nº 1 em avaliações |

O livro é aprovado com **nota média ≥ 85** e **nenhuma página abaixo de 65**.

## Regras aplicadas automaticamente na hora de desenhar

- **Detalhes pequenos viram sólidos.** Qualquer forma fechada menor que a área mínima da
  idade sai pintada de preto, como olhos, narizes e estrelinhas nos livros profissionais.
  Isso fica ligado no tema por `"simplificar_detalhes": true` (padrão).
- **Cenários de página inteira.** Com `"cenarios": true`, cada desenho fica apoiado num
  chão e ganha céu, mar, neve ou espaço com elementos grandes (ver `colorbook/cenas.py`).
- **Contorno externo grosso** (`"contorno_grosso"`, padrão 2,4×): a silhueta da figura
  sai mais grossa que os detalhes internos, como no trabalho de ilustradores.
- **Cenários variados.** Céu e chão mudam de página para página, e figuras largas (galhos,
  trens, carros) ficam só com pedrinhas no chão, para não picotar flores e cercas.
- **Coisas para pintar precisam ser grandes.** Frutas, manchas, bolhas e fumaça que ficam
  pequenas demais viram bolinhas pretas, que parecem buracos. Aumente-as no desenho.
- **Bochechas em risquinhos** (rubor), e não em círculos pequenos.
- **Um desenho por folha**, sempre na página da direita, com o verso em branco.
- **Contornos fechados.** Toda forma para pintar é fechada; linhas soltas só em detalhes
  (bigodes, grama, raios de sol).

## Regras de revisão humana

1. **Uma ideia por página.** A figura principal precisa ser reconhecível em 2 segundos.
2. **Expressões simpáticas.** Rostos sorrindo, nada assustador para a idade.
3. **Nada de marcas ou personagens conhecidos.** Só criações próprias.
4. **Variedade.** Intercale uma atividade a cada 3 ou 4 desenhos e não repita figuras
   (o relatório do auditor lista as repetidas).
5. **Legendas curtas.** De 1 a 3 palavras, que a criança consiga ler ou reconhecer.
6. **Ilustrações importadas** (`importar-ilustracoes`): confira sempre se a limpeza não
   abriu falhas no contorno, o que acontece onde a imagem original tinha sombreado
   encostado na linha. Para essas imagens, a área mínima é mais suave (35% da régua,
   `FATOR_AREA_IMAGEM` em `colorbook/estilo.py`): unhas, ventosas e outros detalhes
   pequenos fazem parte do estilo do desenho.

## Revisão estética

O auditor mede técnica. A beleza é avaliada pelo revisor estético
(`python -m colorbook revisar`), que usa a visão do Claude para dar a cada página uma nota
visual de 1 a 10. Meta: **média ≥ 7,5 e nenhuma página abaixo de 6**.

## Como ajustar a régua

Depois da cópia de prova (veja `PROVA.md`), edite os números em `colorbook/estilo.py`,
rode `python -m colorbook construir-todos` e `python -m colorbook auditar` de novo.
