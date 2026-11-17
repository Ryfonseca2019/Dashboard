# Fábrica de Livros de Colorir

Framework em Python que transforma uma **ideia** em um livro de colorir pronto para
impressão sob demanda: miolo em PDF, capa com lombada calculada e textos de venda
para Amazon KDP, Etsy e Mercado Livre.

```
ideia ──► [Claude] tema.json ──► miolo.pdf + capa.pdf + anuncio.md ──► validação KDP
```

## Instalação

```bash
cd livros_colorir
pip install -r requirements.txt
```

Para conferir as páginas como imagem, instale também o `poppler` (`pdftoppm`).

## Uso rápido

```bash
# Gera os 3 livros de exemplo (primeiros desenhos, mandalas e alfabeto)
python -m colorbook construir-todos

# Gera um livro só
python -m colorbook construir temas/primeiros_desenhos.json

# Imagens PNG das páginas 1 a 12 e da capa, para conferir
python -m colorbook previa saida/primeiros_desenhos --paginas 1-12

# Lista os desenhos disponíveis
python -m colorbook desenhos

# Deixa o Claude criar um tema novo (e já gerar o livro)
export ANTHROPIC_API_KEY=...        # ou: ant auth login
python -m colorbook criar-tema "animais do mar para 3 a 5 anos" --autor "Seu Nome" --construir

# Mede a qualidade de cada página e dá nota de 0 a 100
python -m colorbook auditar

# Revisão estética com a visão do Claude (precisa da chave da API; --simular estima o custo)
python -m colorbook revisar temas/primeiros_desenhos.json --simular

# Folha para testar papel, traço e áreas na impressão (veja PROVA.md)
python -m colorbook folha-teste

# Ilustrações de uma ferramenta de imagens (veja a seção Ilustrações)
python -m colorbook pedidos-ilustracao temas/primeiros_desenhos.json
python -m colorbook importar-ilustracoes minhas_imagens/ temas/primeiros_desenhos.json
```

Cada livro sai em `saida/<id>/`:

| Arquivo | Para quê |
|---|---|
| `miolo.pdf` | Interior do livro: enviar como *manuscript* no KDP |
| `capa.pdf` | Capa completa (contracapa + lombada + capa) com sangria: enviar como *cover* |
| `capa_frente.png` / `capa_miniatura.png` | Prévia da capa e de como ela aparece na busca da Amazon (precisa do `pdftoppm`) |
| `anuncio.md` | Título, descrição, 7 palavras-chave, categorias e a declaração de IA, prontos para copiar |
| `anuncio.json` | Os mesmos dados, para integrar com APIs (Etsy, loja própria etc.) |

## Qualidade

O processo tem quatro camadas:

1. **Guia de estilo** (`ESTILO.md` e `colorbook/estilo.py`): traço mínimo, menor área para
   pintar, quantidade de áreas e ocupação da página, por faixa etária.
2. **Regras aplicadas ao desenhar:** detalhes pequenos demais saem em preto sólido, e
   com `"cenarios": true` cada desenho ocupa a página inteira, com chão e céu.
3. **Auditor técnico** (`python -m colorbook auditar`): mede cada página e gera
   `saida/<id>/qualidade.md` (relatório) e `qualidade.png` (prévia com as notas e as
   áreas pequenas pintadas de vermelho). Meta: média ≥ 85 e nenhuma página abaixo de 65.
4. **Revisor estético** (`python -m colorbook revisar`): envia cada página ao Claude, que
   responde se a figura é reconhecível, dá uma nota visual de 1 a 10, diz se ela é adequada à
   idade e sugere melhorias. Gera `saida/<id>/revisao.md`. Custa cerca de US$ 1 a 2 por livro
   e precisa da chave da API (veja "Chave da API" abaixo).
5. **Cópia de prova** (`PROVA.md`): o roteiro do teste com o livro impresso e uma
   criança de verdade, e como transformar o que você observar em regra.

## O que o livro tem

1. Folha de rosto, direitos autorais, página "Este livro pertence a" e página para testar as cores.
2. **Um desenho por folha, sempre na página da direita, com o verso em branco** (a canetinha não atravessa e não estraga o próximo desenho).
3. Certificado "Parabéns!" no final.
4. Páginas extras "Desenhe o que quiser!" se for preciso chegar ao mínimo de 24 páginas do KDP.

Regras do KDP já aplicadas: margem da costura conforme o número de páginas, fontes embutidas,
espessura da lombada por tipo de papel, texto na lombada só a partir de 79 páginas e
área do código de barras livre na contracapa. O comando `construir` valida tudo no final.

## O tema (JSON)

```json
{
  "id": "primeiros_desenhos",
  "titulo": "Meu Primeiro Livro de Colorir",
  "subtitulo": "Desenhos grandes e fáceis para pintar com giz de cera",
  "autor": "Seu Nome Aqui",
  "faixa_etaria": "2 a 5 anos",
  "formato": "8.5x11",          // 8.5x11 | 8x10 | 8.25x8.25 | a4
  "papel": "branco",            // branco | creme
  "moldura": true,              // borda arredondada em volta do desenho
  "paginas": [
    {"tipo": "desenho", "desenho": "gato", "legenda": "Gatinho"},
    {"tipo": "mandala", "semente": 7, "nivel": 2},
    {"tipo": "letra", "letra": "A", "palavra": "Abelha"},
    {"tipo": "imagem", "arquivo": "imagens/dino.png", "legenda": "Dinossauro"},
    {"tipo": "labirinto", "semente": 3, "nivel": 1, "inicio": "coelho", "fim": "maca"},
    {"tipo": "ligar_pontos", "figura": "estrela", "nivel": 1},
    {"tipo": "diferencas", "desenho": "gato", "semente": 3, "nivel": 1},
    {"tipo": "complete", "desenho": "borboleta"},
    {"tipo": "cubra", "desenho": "peixe"}
  ],
  "capa": {"cor_fundo": "#4FC3F7", "desenhos": ["gato", "sol", "flor", "peixe"],
           "texto_contracapa": "..."},
  "anuncio": {"descricao": "...", "palavras_chave": ["...7 itens..."], "categorias": ["..."]}
}
```

### Tipos de página

- **desenho**: desenhos em traço da biblioteca (`colorbook/desenhos.py`), escritos em código. Hoje são 29: sol, gato, cachorro, coelho, casa, flor, peixe, árvore, borboleta, carro, tartaruga, foguete, passarinho, barco, maçã, coruja, elefante, dinossauro, pinguim, joaninha, caracol, sapo, polvo, trem, balões, sorvete, arco-íris, estrela e coração.
- **mandala**: geradas por algoritmo. Cada `semente` dá uma mandala diferente, e `nivel` vai de 1 (fácil) a 3 (detalhada).
- **letra**: letra vazada, palavra, desenho opcional e linha pontilhada para cobrir.
- **Atividades** (`colorbook/atividades.py`), para intercalar entre os desenhos:
  - **labirinto**: gerado por algoritmo, com um desenho na entrada e outro na saída. Tem sempre um único caminho.
  - **ligar_pontos**: figuras estrela, coração, casa, peixe, foguete e sol.
  - **diferencas**: duas cenas iguais, com 3, 5 ou 7 diferenças conforme o nível.
  - **complete**: metade do desenho, para a criança desenhar a outra metade.
  - **cubra**: desenho em pontilhado cinza para cobrir com o lápis.

  Todas aceitam `nivel` (1 a 3) e `titulo` para trocar a instrução.
- **imagem**: qualquer PNG ou JPG em traço preto, como os que saem de uma API de geração de imagens (DALL·E, Ideogram, Stability...). É por aqui que entram ilustrações mais elaboradas.

### Capa

A capa é gerada a partir do bloco `capa` do tema:

```json
"capa": {
  "cor_fundo": "#4FC3F7",
  "desenhos": ["gato", "dinossauro", "coelho"],
  "texto_contracapa": "..."
}
```

- **Frente:** título com letras coloridas e contorno grosso, faixa com o subtítulo, desenho principal já colorido, dois "adesivos" e um selo com o número de páginas.
- **Contracapa:** lista automática do que tem dentro, montada a partir das páginas do tema.
- **Lombada:** recebe texto só a partir de 79 páginas.
- O primeiro item de `desenhos` também pode ser uma mandala, como `"mandala:104"`.
- Opcionais: `cores_titulo`, `paleta` e `cor_selo`.

Sempre confira o `capa_miniatura.png`: é assim que a capa aparece na busca da Amazon.

### Variações de desenho

No tema, cada página de desenho aceita:

```json
{"tipo": "desenho", "desenho": "gato", "legenda": "Gatinho",
 "brinquedo": "bola", "acessorio": "chapeu", "espelhar": true, "variacao": 2}
```

- `brinquedo`: objeto ao lado da figura (bola, osso, cenoura, balde, pipa ou flor).
- `acessorio`: algo na cabeça (chapeu, laco ou coroa), para as figuras listadas em
  `CABECA`, dentro de `colorbook/cenas.py`.
- `espelhar`: vira a figura para o outro lado.
- `variacao`: troca o céu e o chão sorteados para a página.
- `cena`: força um cenário (campo, mar, mar_superficie, lago, neve, espaco, noite ou nenhum).

No tema todo:
- `"contorno_grosso": 2.4` deixa o contorno externo mais grosso que os detalhes internos
  (0 desliga);
- `"cenarios": true` liga os cenários de página inteira.

Poses alternativas também são desenhos, por exemplo `gato_dormindo`.

### Chave da API do Claude

Só é necessária para `revisar` e `criar-tema`. Crie em https://console.anthropic.com
(**Billing** → créditos pré-pagos; **API Keys** → **Create Key**).

- **No seu computador:** `export ANTHROPIC_API_KEY=sk-ant-...`
- **No Claude Code na nuvem:** abra o menu do ambiente, clique em **Edit**, depois em
  **Environment variables**, e crie `COLORBOOK_ANTHROPIC_KEY=sk-ant-...`. Em seguida, abra
  uma sessão nova. Não use `ANTHROPIC_API_KEY` ali, para não misturar com a conta do
  próprio Claude Code.

A cobrança é por uso, sem mensalidade. Nunca coloque a chave em arquivos do repositório.

### Coleção e mascote

```json
"colecao": {"nome": "Coleção Gizinho", "volume": 1, "mascote": "gizinho"}
```

Com isso:
- o **Gizinho** (um giz de cera simpático) se apresenta na folha de rosto, dá as
  instruções das atividades num balão e assina o certificado;
- a capa ganha o selo "COLEÇÃO GIZINHO · VOL. 1";
- a contracapa lista os outros livros da mesma coleção que estiverem em `temas/`.

Antes de registrar o nome da coleção ou do mascote, confira no INPI se está livre.

### Ilustrações de uma ferramenta de imagens

Para desenhos mais elaborados que os feitos em código:

1. `python -m colorbook pedidos-ilustracao temas/x.json` gera
   `saida/<id>/pedidos_ilustracao.md`, com um pedido (prompt) em inglês por desenho,
   no padrão de livro de colorir para a idade.
2. Gere as imagens em qualquer ferramenta e salve cada uma com o nome do desenho
   (`gato.png`, `dinossauro.png`...).
3. `python -m colorbook importar-ilustracoes pasta/ temas/x.json` limpa cada imagem:
   - preto e branco puro;
   - remove sombreado e sujeira;
   - fecha pequenas falhas;
   - engrossa o traço até o mínimo da idade;
   - preenche de preto as áreas pequenas demais.

   Depois cria `temas/x_ilustrado.json` usando essas imagens. O tema original não muda.
4. Gere e audite o livro novo. **Revise as imagens**: onde havia sombreado encostado no
   contorno, a limpeza pode abrir uma falha na linha.

### Como criar desenhos novos

Abra `colorbook/desenhos.py` e escreva uma função numa grade de 0 a 100 (Y para baixo):

```python
@desenho("pinguim")
def pinguim(p):
    p.elipse(50, 60, 22, 30)        # corpo
    p.elipse(50, 66, 14, 20)        # barriga
    p.circulo(50, 26, 15)           # cabeça
    p.ponto(45, 24); p.ponto(55, 24)
    p.poligono([(46, 30), (54, 30), (50, 36)])  # bico
```

As formas têm preenchimento branco, então quem é desenhado depois "tampa" quem veio antes.
Um bom caminho é pedir ao Claude: *"crie um desenho de pinguim no padrão de desenhos.py"*.

## Fluxo de venda recomendado

| Canal | Como | Automação |
|---|---|---|
| **Amazon KDP** (brochura) | Imprime e entrega sob demanda, sem estoque | Upload manual (o KDP não tem API). Com os arquivos e o `anuncio.md` prontos, leva uns 10 minutos |
| **Etsy** (PDF digital) | Vende o `miolo.pdf` para imprimir em casa | Dá para automatizar pela API do Etsy usando o `anuncio.json` |
| **Loja própria + Lulu Print API** | Pedido na loja → Lulu imprime e envia | Totalmente automatizável (próximo passo) |
| **Mercado Livre / Shopee** | Exige gráfica nacional sob demanda | Depende da integração da gráfica escolhida |

### Cuidados

- **Declaração de IA no KDP**: o `anuncio.md` já traz a resposta sugerida. Responda "sim" para conteúdo gerado por IA.
- **Marcas registradas**: o gerador avisa se o anúncio citar personagens conhecidos. Não use.
- **Revise sempre** as prévias antes de publicar. Peça uma **cópia de prova** (*proof copy*) no KDP antes de liberar a venda.
- Confira as regras atuais do KDP (margens, lombada, preços). Elas mudam de tempos em tempos e os valores ficam em `colorbook/specs.py`.

## Estrutura

```
livros_colorir/
├── colorbook/
│   ├── specs.py        # medidas e regras do KDP (formatos, lombada, margens)
│   ├── caneta.py       # motor de desenho em traço (grade 0–100)
│   ├── desenhos.py     # biblioteca de desenhos
│   ├── mandalas.py     # mandalas por algoritmo
│   ├── paginas.py      # tipos de página (desenho, mandala, letra, imagem)
│   ├── atividades.py   # labirinto, ligar os pontos, diferenças, complete, cubra
│   ├── miolo.py        # monta o PDF do interior
│   ├── capa.py         # monta a capa com lombada e as miniaturas
│   ├── cenas.py        # cenários de página inteira (campo, mar, neve, espaço...)
│   ├── colecao.py      # coleção, mascote e balões de fala
│   ├── estilo.py       # guia de estilo em números (régua do auditor)
│   ├── auditar.py      # auditor de qualidade (técnico)
│   ├── revisar.py      # revisor estético com a visão do Claude
│   ├── claude_cliente.py # leitura da chave e conexão com a API do Claude
│   ├── folha_teste.py  # folha de teste de impressão
│   ├── ilustracoes.py  # pedidos de ilustração e limpeza de imagens
│   ├── anuncio.py      # textos de venda + limites de cada marketplace
│   ├── validar.py      # checagem final contra as regras do KDP
│   ├── claude_tema.py  # cria temas novos com a API do Claude
│   └── cli.py          # linha de comando
├── temas/              # um JSON por livro
└── saida/              # PDFs gerados (fora do git)
```

## Próximos passos

- [ ] Ligar uma API de imagens direto ao `pedidos-ilustracao` (o fluxo de importação já está pronto).
- [ ] Exportar para a **Lulu** (a lombada e a capa têm fórmula própria) e criar pedidos pela Lulu Print API.
- [ ] Publicar o PDF digital no Etsy pela API.
- [ ] Livro personalizado com o nome da criança (gerado na hora do pedido).
- [ ] Mais desenhos na biblioteca (fundo do mar, profissões, folclore brasileiro).
