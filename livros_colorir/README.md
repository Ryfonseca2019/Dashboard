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
```

Cada livro sai em `saida/<id>/`:

| Arquivo | Para quê |
|---|---|
| `miolo.pdf` | Interior do livro: enviar como *manuscript* no KDP |
| `capa.pdf` | Capa completa (contracapa + lombada + capa) com sangria: enviar como *cover* |
| `anuncio.md` | Título, descrição, 7 palavras-chave, categorias e a declaração de IA, prontos para copiar |
| `anuncio.json` | Os mesmos dados, para integrar com APIs (Etsy, loja própria etc.) |

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
    {"tipo": "imagem", "arquivo": "imagens/dino.png", "legenda": "Dinossauro"}
  ],
  "capa": {"cor_fundo": "#4FC3F7", "desenhos": ["gato", "sol", "flor", "peixe"],
           "texto_contracapa": "..."},
  "anuncio": {"descricao": "...", "palavras_chave": ["...7 itens..."], "categorias": ["..."]}
}
```

### Tipos de página

- **desenho**: desenhos em traço da biblioteca (`colorbook/desenhos.py`), escritos em código. Hoje são 19: sol, gato, casa, flor, peixe, árvore, borboleta, carro, tartaruga, foguete, passarinho, barco, maçã, coruja, balões, sorvete, arco-íris, estrela e coração.
- **mandala**: geradas por algoritmo. Cada `semente` dá uma mandala diferente, e `nivel` vai de 1 (fácil) a 3 (detalhada).
- **letra**: letra vazada, palavra, desenho opcional e linha pontilhada para cobrir.
- **imagem**: qualquer PNG ou JPG em traço preto, como os que saem de uma API de geração de imagens (DALL·E, Ideogram, Stability...). É por aqui que entram ilustrações mais elaboradas.

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
│   ├── miolo.py        # monta o PDF do interior
│   ├── capa.py         # monta a capa com lombada
│   ├── anuncio.py      # textos de venda + limites de cada marketplace
│   ├── validar.py      # checagem final contra as regras do KDP
│   ├── claude_tema.py  # cria temas novos com a API do Claude
│   └── cli.py          # linha de comando
├── temas/              # um JSON por livro
└── saida/              # PDFs gerados (fora do git)
```

## Próximos passos

- [ ] Integrar uma API de geração de imagens (o tipo de página `imagem` já recebe o resultado).
- [ ] Exportar para a **Lulu** (a lombada e a capa têm fórmula própria) e criar pedidos pela Lulu Print API.
- [ ] Publicar o PDF digital no Etsy pela API.
- [ ] Livro personalizado com o nome da criança (gerado na hora do pedido).
- [ ] Mais desenhos na biblioteca (dinossauros, fundo do mar, profissões, folclore brasileiro).
