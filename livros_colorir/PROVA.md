# Roteiro da cópia de prova

A prova impressa é o único jeito de saber como o livro fica no papel do KDP e nas mãos
de uma criança. Faça isso **antes de publicar o primeiro livro** e sempre que mudar
algo importante nas regras de estilo.

## 1. Antes de pedir a prova (em casa, 10 minutos)

1. Gere a folha de teste: `python -m colorbook folha-teste` → `saida/folha_teste.pdf`.
2. Imprima a folha e uma página de cada tipo do livro (desenho, labirinto, ligue os
   pontos...) numa impressora comum.
3. Peça para a criança pintar a folha de teste (seção 2) e anote o menor círculo que
   ela pintou sem sair muito da linha.

## 2. Pedir a prova no KDP

1. Cadastre o livro no KDP como rascunho (manuscrito `miolo.pdf` + capa `capa.pdf`).
2. Na página do livro, peça uma cópia de prova (*proof copy*). Ela tem uma faixa
   "Not for resale" e custa só a impressão e o frete.
3. Junto com o livro, imprima de novo a folha de teste e leve as duas para o teste.

## 3. O que conferir na prova

**Papel e impressão**
- [ ] Traço: qual a linha mais fina da folha de teste que ainda aparece bem?
- [ ] Pontilhado ("cubra"): o tom de cinza ficou visível sem parecer traço final?
- [ ] Canetinha e marcador atravessaram o papel? (Por isso o verso fica em branco.)
- [ ] O desenho ficou longe da costura do livro?

**Capa**
- [ ] As cores ficaram parecidas com a tela? (Costumam escurecer um pouco.)
- [ ] O título lê bem de longe e a lombada está alinhada?

**Com a criança** (o teste mais importante)
- [ ] Ela reconheceu as figuras sozinha?
- [ ] Quais páginas ela escolheu primeiro? E quais pulou?
- [ ] Onde ela se frustrou (área pequena, labirinto difícil, instrução confusa)?
- [ ] Quanto tempo ela ficou entretida?
- [ ] O que os pais acharam da quantidade de páginas e do preço?

## 4. Transformar o que viu em regra

| Observação | O que ajustar |
|---|---|
| Linha de X pt quase sumiu | `traco_min_pt` em `colorbook/estilo.py` |
| Criança não pintou círculos de Y cm² | `area_min_cm2` |
| Pontilhado fraco ou forte demais | cor do pontilhado em `colorbook/atividades.py` (`CINZA_TRACO`) |
| Página "chata" ou difícil demais | troque o desenho ou o nível da atividade no tema |
| Cores da capa escuras demais | clareie `cor_fundo` no tema |

Depois rode `python -m colorbook construir-todos` e `python -m colorbook auditar` de novo.
Guarde as anotações. Elas valem para todos os próximos livros.
