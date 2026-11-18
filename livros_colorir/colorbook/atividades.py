"""Páginas de atividade: dão mais valor ao livro e quebram a repetição.

Tipos (use no JSON do tema):

  {"tipo": "labirinto", "semente": 1, "nivel": 1, "inicio": "coelho", "fim": "maca",
   "titulo": "Ajude o coelho a chegar na maçã!"}
  {"tipo": "ligar_pontos", "figura": "estrela", "nivel": 1}
  {"tipo": "diferencas", "desenho": "gato", "semente": 3, "nivel": 1}
  {"tipo": "complete", "desenho": "borboleta"}
  {"tipo": "cubra", "desenho": "peixe"}

`nivel` vai de 1 (2 a 5 anos) a 3 (7 a 10 anos). `semente` muda o resultado
mantendo-o reproduzível. Toda página tem um título com a instrução, que pode
ser trocado com "titulo".
"""
from __future__ import annotations

import math
import random

from reportlab.lib.colors import Color, black
from reportlab.pdfgen.canvas import Canvas

from .caneta import Caneta
from .desenhos import DESENHOS, desenhar
from .fonts import FONTE, FONTE_NEGRITO

Area = tuple[float, float, float, float]
CINZA_TRACO = Color(0.55, 0.55, 0.55)


def _titulo(c: Canvas, area: Area, texto: str, tam: float = 26,
            mascote: str | None = None) -> Area:
    """Escreve a instrução no topo e devolve a área que sobra. Com mascote, ele
    aparece à esquerda "falando" a instrução num balão."""
    x, y, w, h = area
    if mascote:
        from .colecao import balao

        lado = 74
        desenhar(mascote, Caneta(c, x, y + h - lado, lado, lado, espessura=2))
        tam_b = 17
        alt = balao(c, x + lado + 20, y + h - 4, w - lado - 20, texto, tam=tam_b)
        return x, y, w, h - max(lado, alt) - 18
    while c.stringWidth(texto, FONTE_NEGRITO, tam) > w and tam > 12:
        tam -= 1
    c.setFillColor(black)
    c.setFont(FONTE_NEGRITO, tam)
    c.drawCentredString(x + w / 2, y + h - tam, texto)
    folga = tam + 22
    return x, y, w, h - folga


NOMES = {"maca": "maçã", "arvore": "árvore", "baloes": "balões", "arco_iris": "arco-íris",
         "coracao": "coração"}
FEMININOS = {"maca", "flor", "arvore", "borboleta", "tartaruga", "coruja", "casa", "estrela",
             "joaninha"}


def _com_artigo(desenho: str) -> str:
    """'o coelho', 'a maçã', 'os balões'."""
    nome = NOMES.get(desenho, desenho.replace("_", " "))
    if desenho == "baloes":
        return f"os {nome}"
    return f"{'a' if desenho in FEMININOS else 'o'} {nome}"


# ----------------------------------------------------------------------------- labirinto
def _gerar_labirinto(cols: int, lins: int, rnd: random.Random):
    """Labirinto perfeito (um único caminho) pelo método da busca em profundidade.
    Devolve, para cada célula, o conjunto de paredes abertas (N, S, L, O)."""
    abertas = [[set() for _ in range(cols)] for _ in range(lins)]
    visitada = [[False] * cols for _ in range(lins)]
    pilha = [(0, 0)]
    visitada[0][0] = True
    passos = {"N": (0, -1, "S"), "S": (0, 1, "N"), "L": (1, 0, "O"), "O": (-1, 0, "L")}
    while pilha:
        cx, cy = pilha[-1]
        vizinhos = []
        for d, (dx, dy, oposto) in passos.items():
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < cols and 0 <= ny < lins and not visitada[ny][nx]:
                vizinhos.append((d, nx, ny, oposto))
        if not vizinhos:
            pilha.pop()
            continue
        d, nx, ny, oposto = rnd.choice(vizinhos)
        abertas[cy][cx].add(d)
        abertas[ny][nx].add(oposto)
        visitada[ny][nx] = True
        pilha.append((nx, ny))
    return abertas


def pagina_labirinto(c: Canvas, area: Area, pag: dict) -> None:
    inicio, fim = pag.get("inicio", "coelho"), pag.get("fim", "maca")
    area = _titulo(c, area, pag.get("titulo",
                                    f"Ajude {_com_artigo(inicio)} a chegar até {_com_artigo(fim)}!"),
                   mascote=pag.get("_mascote"))
    x, y, w, h = area
    nivel = max(1, min(3, int(pag.get("nivel", 1))))
    cols, lins = {1: (6, 7), 2: (9, 11), 3: (13, 16)}[nivel]
    rnd = random.Random(int(pag.get("semente", 1)))
    abertas = _gerar_labirinto(cols, lins, rnd)

    figura = min(w * 0.34, 170)
    alto = figura * 0.75
    lado = min(w / cols, (h - 2 * alto - 8) / lins)
    lw, lh = cols * lado, lins * lado
    x0 = x + (w - lw) / 2
    y_topo = y + (h + lh) / 2

    # Figuras de entrada (acima, à esquerda) e saída (abaixo, à direita): ilustração
    # importada quando houver, senão o desenho em código.
    for ponta, nome, ax, ay in (("inicio", inicio, x0 - figura * 0.2, y_topo + 2),
                                ("fim", fim, x0 + lw - figura * 0.8, y_topo - lh - alto - 2)):
        if pag.get(f"_arquivo_{ponta}_abs"):
            _imagem_na_area(c, pag[f"_arquivo_{ponta}_abs"], (ax, ay, figura, alto))
        else:
            desenhar(nome, Caneta(c, ax, ay, figura, alto))

    c.setStrokeColor(black)
    c.setLineWidth({1: 5, 2: 4, 3: 3}[nivel])
    c.setLineCap(1)
    for j in range(lins):
        for i in range(cols):
            ax = x0 + i * lado
            ay = y_topo - j * lado
            aberto = abertas[j][i]
            entrada = (i == 0 and j == 0)
            saida = (i == cols - 1 and j == lins - 1)
            if "N" not in aberto and not entrada:
                c.line(ax, ay, ax + lado, ay)
            if "O" not in aberto:
                c.line(ax, ay, ax, ay - lado)
            if j == lins - 1 and not saida:
                c.line(ax, ay - lado, ax + lado, ay - lado)
            if i == cols - 1:
                c.line(ax + lado, ay, ax + lado, ay - lado)


# ----------------------------------------------------------------------------- ligar os pontos
def _poligono_estrela():
    pts = []
    for i in range(10):
        r = 46 if i % 2 == 0 else 20
        a = math.radians(-90 + i * 36)
        pts.append((50 + r * math.cos(a), 54 + r * math.sin(a)))
    return pts


def _contorno_coracao(n):
    """Contorno do coração com pontos espaçados por igual, começando na ponta de baixo."""
    denso = []
    for k in range(400):
        t = math.pi + 2 * math.pi * k / 400
        xx = 16 * math.sin(t) ** 3
        yy = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        denso.append((50 + xx * 2.7, 48 - yy * 2.7))
    # Espaça os pontos pelo comprimento do contorno (sem amontoar na ponta e no "v").
    acum = [0.0]
    for a, b in zip(denso, denso[1:] + denso[:1]):
        acum.append(acum[-1] + math.dist(a, b))
    total, pts, j = acum[-1], [], 0
    for k in range(n):
        alvo = total * k / n
        while acum[j + 1] < alvo:
            j += 1
        pts.append(denso[j])
    return pts


def _poligono_sol():
    pts = []
    for i in range(16):
        r = 46 if i % 2 == 0 else 32
        a = math.radians(-90 + i * 22.5)
        pts.append((50 + r * math.cos(a), 50 + r * math.sin(a)))
    return pts


FIGURAS_PONTOS = {
    # nome: (pontos do contorno, detalhes desenhados prontos, legenda)
    "estrela": (lambda n: _reamostrar(_poligono_estrela(), n),
                lambda p: (p.ponto(42, 56, 2.4), p.ponto(58, 56, 2.4), p.sorriso(50, 60, 6)),
                "uma estrela"),
    "coracao": (_contorno_coracao, lambda p: None, "um coração"),
    "casa": (lambda n: _reamostrar([(20, 88), (20, 48), (50, 18), (64, 31), (64, 22), (72, 22),
                                    (72, 39), (80, 48), (80, 88)], n),
             lambda p: (p.retangulo(43, 64, 57, 88, cheio=False),
                        p.retangulo(26, 54, 38, 66, cheio=False),
                        p.retangulo(62, 54, 74, 66, cheio=False)),
             "uma casa"),
    "peixe": (lambda n: _reamostrar(
        [(10, 50)] + [(42 + 32 * math.cos(math.radians(a)), 50 - 20 * math.sin(math.radians(a)))
                      for a in range(150, 30, -20)]
        + [(90, 30), (84, 50), (90, 70)]
        + [(42 + 32 * math.cos(math.radians(a)), 50 - 20 * math.sin(math.radians(a)))
           for a in range(-30, -150, -20)], n),
              lambda p: (p.circulo(26, 46, 4, cheio=False), p.ponto(25, 46, 2)),
              "um peixe"),
    "foguete": (lambda n: _reamostrar([(50, 6), (60, 22), (62, 56), (76, 78), (60, 76),
                                       (58, 84), (42, 84), (40, 76), (24, 78), (38, 56),
                                       (40, 22)], n),
                lambda p: (p.circulo(50, 40, 7, cheio=False),),
                "um foguete"),
    "sol": (lambda n: _reamostrar(_poligono_sol(), n),
            lambda p: (p.ponto(42, 46, 2.4), p.ponto(58, 46, 2.4), p.sorriso(50, 52, 8)),
            "um sol"),
}


def _reamostrar(cantos, n):
    """Distribui ~n pontos pelo contorno, sempre mantendo os cantos."""
    lados = list(zip(cantos, cantos[1:] + cantos[:1]))
    tamanhos = [math.dist(a, b) for a, b in lados]
    total = sum(tamanhos)
    pts = []
    for (a, b), t in zip(lados, tamanhos):
        partes = max(1, round(t / total * n))
        for k in range(partes):
            f = k / partes
            pts.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return pts


def pagina_ligar_pontos(c: Canvas, area: Area, pag: dict) -> None:
    figura = pag.get("figura", "estrela")
    nivel = max(1, min(3, int(pag.get("nivel", 1))))
    gerar, detalhes, _ = FIGURAS_PONTOS[figura]
    n = {1: 10, 2: 20, 3: 32}[nivel]
    pts = gerar(n)
    area = _titulo(c, area, pag.get("titulo", f"Ligue os pontos de 1 a {len(pts)}!"),
                   mascote=pag.get("_mascote"))
    x, y, w, h = area
    c.setFont(FONTE, 11)
    c.setFillColor(black)
    c.drawCentredString(x + w / 2, y + 4, "Descubra o que aparece e depois pinte!")
    p = Caneta(c, x, y + 24, w, h - 24, espessura=2.6)
    detalhes(p)
    cx = sum(px for px, _ in pts) / len(pts)
    cy = sum(py for _, py in pts) / len(pts)
    tam = {1: 16, 2: 12, 3: 10}[nivel]
    for i, (px, py) in enumerate(pts, 1):
        p.ponto(px, py, 1.3)
        ang = math.atan2(py - cy, px - cx)
        lx, ly = px + 4.2 * math.cos(ang), py + 4.2 * math.sin(ang)
        c.setFillColor(black)
        c.setFont(FONTE_NEGRITO if i == 1 else FONTE, tam)
        c.drawCentredString(p.X(lx), p.Y(ly) - tam * 0.35, str(i))


# ----------------------------------------------------------------------------- diferenças
ENFEITES = ["estrela", "coracao", "maca", "flor", "sol", "borboleta", "baloes", "joaninha",
            "sorvete", "peixe", "passarinho", "arvore"]


def pagina_diferencas(c: Canvas, area: Area, pag: dict) -> None:
    nivel = max(1, min(3, int(pag.get("nivel", 1))))
    qtd = pag.get("qtd_diferencas") or {1: 3, 2: 5, 3: 7}[nivel]
    area = _titulo(c, area, pag.get("titulo", f"Encontre as {qtd} diferenças!"),
                   mascote=pag.get("_mascote"))
    x, y, w, h = area
    if pag.get("_arquivo_a_abs") and pag.get("_arquivo_b_abs"):
        # Ilustrações importadas: cena A em cima e cena B embaixo, cada uma numa moldura.
        caixa_h = (h - 20) / 2
        for k, chave in enumerate(("_arquivo_a_abs", "_arquivo_b_abs")):
            cy = y + caixa_h + 20 if k == 0 else y
            c.setStrokeColor(black)
            c.setLineWidth(2.5)
            c.roundRect(x, cy, w, caixa_h, 16, stroke=1, fill=0)
            _imagem_na_area(c, pag[chave], (x + 10, cy + 10, w - 20, caixa_h - 20))
        return
    rnd = random.Random(int(pag.get("semente", 1)))
    base = pag.get("desenho", "gato")
    lugares = 8 if nivel > 1 else 6
    opcoes = [e for e in ENFEITES if e != base]
    enfeites = [rnd.choice(opcoes) for _ in range(lugares)]
    mudancas = set(rnd.sample(range(lugares), qtd))
    trocas = {i: rnd.choice([None] + [e for e in opcoes if e != enfeites[i]]) for i in mudancas}

    caixa_h = (h - 24) / 2
    for k, cy in enumerate((y + caixa_h + 24, y)):
        c.setStrokeColor(black)
        c.setLineWidth(2.5)
        c.roundRect(x, cy, w, caixa_h, 16, stroke=1, fill=0)
        lado = caixa_h - 20
        desenhar(base, Caneta(c, x + (w - lado) / 2, cy + 10, lado, lado, espessura=2.6))
        col_w = (w - lado) / 2 - 12
        por_col = lugares // 2
        tam = min(col_w, (caixa_h - 20) / por_col)
        for i in range(lugares):
            nome = enfeites[i] if k == 0 or i not in trocas else trocas[i]
            if not nome:
                continue
            coluna, linha = divmod(i, por_col)
            ex = x + 8 + (col_w - tam) / 2 if coluna == 0 else x + w - 8 - (col_w + tam) / 2
            ey = cy + caixa_h - 10 - (linha + 1) * tam
            desenhar(nome, Caneta(c, ex, ey, tam, tam, espessura=1.8))


# ----------------------------------------------------------------------------- complete / cubra
def _imagem_na_area(c: Canvas, caminho: str, area: Area, so_esquerda: bool = False):
    """Desenha uma imagem centralizada na área; devolve o retângulo ocupado."""
    from reportlab.lib.utils import ImageReader

    img = ImageReader(caminho)
    iw, ih = img.getSize()
    x, y, w, h = area
    escala = min(w / iw, h / ih)
    dw, dh = iw * escala, ih * escala
    ix, iy = x + (w - dw) / 2, y + (h - dh) / 2
    c.saveState()
    if so_esquerda:
        caminho_recorte = c.beginPath()
        caminho_recorte.rect(ix - 2, iy - 2, dw / 2 + 2, dh + 4)
        c.clipPath(caminho_recorte, stroke=0, fill=0)
    c.drawImage(img, ix, iy, dw, dh, mask="auto")
    c.restoreState()
    return ix, iy, dw, dh


def pagina_complete(c: Canvas, area: Area, pag: dict) -> None:
    area = _titulo(c, area, pag.get("titulo", "Desenhe a outra metade e depois pinte!"),
                   mascote=pag.get("_mascote"))
    if pag.get("_arquivo_abs"):  # ilustração importada, cortada ao meio
        ix, iy, dw, dh = _imagem_na_area(c, pag["_arquivo_abs"], area, so_esquerda=True)
        c.setStrokeColor(CINZA_TRACO)
        c.setLineWidth(1.2)
        c.setDash(6, 6)
        c.line(ix + dw / 2, iy, ix + dw / 2, iy + dh)
        c.setDash()
        return
    x, y, w, h = area
    p = Caneta(c, x, y, w, h)
    meio = p.X(50)
    c.saveState()
    caminho = c.beginPath()
    caminho.rect(x - 50, y - 50, meio - x + 50, h + 100)
    c.clipPath(caminho, stroke=0, fill=0)
    desenhar(pag.get("desenho", "borboleta"), p)
    c.restoreState()
    c.setStrokeColor(CINZA_TRACO)
    c.setLineWidth(1.2)
    c.setDash(6, 6)
    c.line(meio, p.Y(0), meio, p.Y(100))
    c.setDash()


def pagina_cubra(c: Canvas, area: Area, pag: dict) -> None:
    area = _titulo(c, area, pag.get("titulo", "Cubra o pontilhado e depois pinte!"),
                   mascote=pag.get("_mascote"))
    if pag.get("_arquivo_abs"):  # versão pontilhada da ilustração importada
        _imagem_na_area(c, pag["_arquivo_abs"], area)
        return
    desenhar(pag.get("desenho", "peixe"),
             Caneta(c, *area, espessura=2.4, cor_traco=CINZA_TRACO, tracejado=(5, 5)))
    c.setDash()


TIPOS = {
    "labirinto": pagina_labirinto,
    "ligar_pontos": pagina_ligar_pontos,
    "diferencas": pagina_diferencas,
    "complete": pagina_complete,
    "cubra": pagina_cubra,
}


def descrever(paginas: list[dict]) -> dict[str, int]:
    """Conta as páginas por tipo, para a contracapa e o anúncio."""
    contagem: dict[str, int] = {}
    for pag in paginas:
        t = pag.get("tipo", "desenho")
        contagem[t] = contagem.get(t, 0) + 1
    return contagem


assert set(ENFEITES) <= set(DESENHOS), "Enfeite sem desenho correspondente"
