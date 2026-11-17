"""Cenários: transformam a figura solta numa página inteira para pintar.

A figura é desenhada grande e "apoiada no chão"; o espaço que sobra em cima vira
céu (ou água, ou espaço) com elementos grandes e fáceis de pintar. Assim a
página não fica com metade em branco.

Ative no tema com  "cenarios": true. Cada desenho tem um cenário padrão
(CENA_PADRAO); dá para trocar por página com  "cena": "mar"  ou  "cena": "nenhum".
"""
from __future__ import annotations

import copy
import math

from reportlab.lib.colors import black, white
from reportlab.pdfgen.canvas import Canvas

from .caneta import Caneta
from .desenhos import _nuvem, desenhar

CENA_PADRAO = {
    **dict.fromkeys(["gato", "cachorro", "coelho", "casa", "flor", "arvore", "tartaruga",
                     "elefante", "dinossauro", "carro", "trem", "caracol", "joaninha",
                     "borboleta", "passarinho", "coruja", "baloes", "sorvete", "maca"], "campo"),
    **dict.fromkeys(["peixe", "polvo"], "mar"),
    "barco": "mar_superficie",
    "sapo": "lago",
    "pinguim": "neve",
    "gato_dormindo": "noite",
    **dict.fromkeys(["foguete", "estrela"], "espaco"),
    # Desenhos que já ocupam a página sozinhos ficam sem cenário.
    **dict.fromkeys(["sol", "arco_iris", "coracao"], "nenhum"),
}
CENAS = {"campo", "mar", "mar_superficie", "lago", "neve", "espaco", "noite", "nenhum"}

# Figuras largas cobrem parte de flores, cercas e arbustos e deixam pontas picotadas:
# para elas o chão fica só com pedrinhas (que ficam abaixo da linha do chão).
FIGURAS_LARGAS = {"passarinho", "coruja", "caracol", "elefante", "trem", "carro",
                  "tartaruga", "dinossauro"}

LINHA_DO_CHAO = 0.91  # na grade 0–100 dos desenhos, onde os pés costumam ficar


def _quadro(c: Canvas, cx: float, cy: float, lado: float, espessura: float) -> Caneta:
    return Caneta(c, cx - lado / 2, cy - lado / 2, lado, lado, espessura=espessura)


def _sol(c, cx, cy, r, esp):
    p = _quadro(c, cx, cy, r * 2.4, esp)
    for i in range(10):
        a = math.radians(i * 36)
        p.linha(50 + 30 * math.cos(a), 50 + 30 * math.sin(a),
                50 + 46 * math.cos(a), 50 + 46 * math.sin(a))
    p.circulo(50, 50, 24)
    p.ponto(43, 46, 2.5)
    p.ponto(57, 46, 2.5)
    p.sorriso(50, 52, 9)


def _chao_ondulado(c, x, y_linha, w, esp, amplitude=4):
    """Linha do chão levemente ondulada, com o espaço abaixo pintado de branco."""
    caminho = c.beginPath()
    caminho.moveTo(x, y_linha)
    passos = 6
    for i in range(passos):
        x0 = x + w * i / passos
        x1 = x + w * (i + 1) / passos
        caminho.curveTo(x0 + (x1 - x0) / 3, y_linha + amplitude * (1 if i % 2 else -1),
                        x0 + 2 * (x1 - x0) / 3, y_linha + amplitude * (1 if i % 2 else -1),
                        x1, y_linha)
    c.setStrokeColor(black)
    c.setLineWidth(esp)
    c.setLineCap(1)
    c.drawPath(caminho, stroke=1, fill=0)


def _tufos(c, x, y, w, esp, passo=64):
    """Tufos de grama como folhinhas soltas que saem de um ponto do chão.
    Não fecham nenhuma área (triângulos minúsculos seriam impossíveis de pintar)."""
    c.setLineWidth(esp)
    c.setStrokeColor(black)
    c.setLineCap(1)
    for i in range(int(w // passo)):
        tx = x + 24 + i * passo
        if x + w * 0.2 < tx < x + w * 0.8:
            continue  # embaixo da figura os tufos fechariam frestas com a base dela
        c.lines([(tx, y, tx - 9, y + 14), (tx, y, tx, y + 19), (tx, y, tx + 9, y + 14)])


def _pedras(c, x, y_topo, w, h_faixa, esp):
    c.setStrokeColor(black)
    c.setFillColor(white)
    c.setLineWidth(esp)
    for fx, fr in ((0.1, 1.0), (0.88, 0.85)):
        rx, ry = 34 * fr, 15 * fr
        c.ellipse(x + w * fx - rx, y_topo - h_faixa * 0.55 - ry,
                  x + w * fx + rx, y_topo - h_faixa * 0.55 + ry, stroke=1, fill=1)


def _alga(c, x_base, y_base, altura, esp):
    """Alga alta e ondulada, desenhada como faixa com contorno (pintável por dentro)."""
    lado = altura
    p = Caneta(c, x_base - lado / 2, y_base, lado, lado, espessura=esp)
    p.tubo([("M", 50, 100), ("C", 30, 75, 70, 55, 48, 30), ("C", 36, 18, 56, 8, 50, 2)],
           largura=12)


def _concha(c, cx, cy, tam, esp):
    """Estrela-do-mar na areia (fatias de concha davam áreas finas demais)."""
    p = _quadro(c, cx, cy, tam, esp)
    p.estrela(50, 55, 46, 24, giro=-90)
    p.ponto(43, 52, 2.5)
    p.ponto(57, 52, 2.5)


def _estrela_espaco(c, cx, cy, tam, esp):
    _quadro(c, cx, cy, tam, esp).estrela(50, 50, 45, 21)


def _planeta(c, cx, cy, r, esp):
    p = _quadro(c, cx, cy, r * 2.6, esp)
    p.elipse(50, 52, 48, 15, angulo=-15, cheio=False)
    p.circulo(50, 50, 26)  # tampa a parte de trás do anel
    p.caminho([("M", 6, 58), ("C", 30, 70, 70, 54, 94, 42)], cheio=False, fechar=False)


def _lua(c, cx, cy, r, esp):
    p = _quadro(c, cx, cy, r * 2.2, esp)
    p.caminho([("M", 60, 6), ("C", 10, 10, 10, 90, 60, 94), ("C", 32, 76, 32, 24, 60, 6)])
    p.ponto(40, 46, 2.2)
    p.arco(42, 56, 5, 210, 330)


def _floco(c, cx, cy, r, esp):
    c.setStrokeColor(black)
    c.setLineWidth(esp)
    for i in range(3):
        a = math.radians(i * 60)
        c.line(cx - r * math.cos(a), cy - r * math.sin(a), cx + r * math.cos(a),
               cy + r * math.sin(a))
    c.setFillColor(white)
    c.circle(cx, cy, r * 0.3, stroke=1, fill=1)


# ----------------------------------------------------------------------------- variações do céu
def _passarinhos(c, cx, cy, tam, esp):
    """Passarinhos ao longe, em "v" (linhas soltas, não criam áreas)."""
    c.setStrokeColor(black)
    c.setLineWidth(esp)
    for dx, dy, f in ((0, 0, 1.0), (tam * 0.9, tam * 0.35, 0.75)):
        x0, y0, t = cx + dx, cy + dy, tam * 0.5 * f
        caminho = c.beginPath()
        caminho.moveTo(x0 - t, y0 + t * 0.35)
        caminho.curveTo(x0 - t * 0.5, y0 + t * 0.6, x0 - t * 0.15, y0 + t * 0.3, x0, y0)
        caminho.curveTo(x0 + t * 0.15, y0 + t * 0.3, x0 + t * 0.5, y0 + t * 0.6, x0 + t, y0 + t * 0.35)
        c.drawPath(caminho, stroke=1, fill=0)


def _arco_iris_pequeno(c, cx, cy, tam, esp):
    p = _quadro(c, cx, cy, tam, esp)
    for r in (44, 34, 24):
        p.caminho([("M", 50 - r, 72), ("C", 50 - r, 72 - r * 1.33, 50 + r, 72 - r * 1.33,
                                        50 + r, 72)])
    p.caminho([("M", 36, 72), ("C", 36, 56, 64, 56, 64, 72)])
    _nuvem(p, 12, 72, 0.75)
    _nuvem(p, 88, 72, 0.75)


def _baloes_longe(c, cx, cy, tam, esp):
    p = _quadro(c, cx, cy, tam, esp)
    for bx, by in ((36, 34), (62, 28)):
        p.caminho([("M", bx, by + 20), ("C", bx + 4, by + 40, bx - 6, by + 52, bx, by + 66)],
                  fechar=False, espessura=esp * 0.7)
        p.elipse(bx, by, 14, 18)


def _ceu_campo(c, x, w, meio, faixa, esp, variante):
    tam_nuvem = min(faixa * 1.25, w * 0.4)
    r_sol = min(faixa * 0.5, w * 0.14)
    if variante == 0:      # sol à direita e duas nuvens
        _sol(c, x + w - r_sol * 1.25, meio, r_sol, esp)
        for fx in (0.2, 0.55):
            _nuvem(_quadro(c, x + w * fx, meio, tam_nuvem, esp), 50, 50, 1.9)
    elif variante == 1:    # sol à esquerda, nuvem grande e passarinhos
        _sol(c, x + r_sol * 1.25, meio, r_sol, esp)
        _nuvem(_quadro(c, x + w * 0.72, meio, tam_nuvem * 1.15, esp), 50, 50, 1.9)
        _passarinhos(c, x + w * 0.38, meio, faixa * 0.35, esp)
    elif variante == 2:    # arco-íris pequeno
        _arco_iris_pequeno(c, x + w * 0.3, meio, min(faixa * 1.5, w * 0.48), esp)
        _sol(c, x + w - r_sol * 1.25, meio, r_sol * 0.9, esp)
    else:                  # balões ao longe
        _baloes_longe(c, x + w * 0.16, meio, faixa * 1.05, esp)
        _nuvem(_quadro(c, x + w * 0.52, meio, tam_nuvem, esp), 50, 50, 1.9)
        _sol(c, x + w - r_sol * 1.25, meio, r_sol * 0.9, esp)


# ----------------------------------------------------------------------------- variações do chão
def _flor_grande(c, cx, y_chao, alt, esp):
    """Tulipa: uma corola grande (fácil de pintar) em vez de pétalas pequenas."""
    p = Caneta(c, cx - alt / 2, y_chao - alt * 0.02, alt, alt, espessura=esp)
    p.linha(50, 100, 50, 46)
    p.caminho([("M", 50, 80), ("C", 62, 62, 82, 62, 88, 66), ("C", 80, 84, 62, 88, 50, 80)])
    p.caminho([("M", 26, 14), ("L", 38, 26), ("L", 50, 8), ("L", 62, 26), ("L", 74, 14),
               ("L", 74, 34), ("C", 74, 56, 26, 56, 26, 34)])


def _arbusto(c, cx, y_chao, larg, esp):
    p = Caneta(c, cx - larg / 2, y_chao - larg * 0.2, larg, larg, espessura=esp)
    p.caminho([("M", 6, 80), ("C", 0, 60, 14, 48, 26, 54), ("C", 28, 36, 50, 32, 56, 46),
               ("C", 66, 34, 90, 40, 88, 58), ("C", 100, 62, 98, 80, 90, 80), ("L", 6, 80)])


def _cerca(c, x, y_chao, w, alt, esp):
    """Cerca de madeira ao fundo, atravessando a página (atrás da figura)."""
    c.setStrokeColor(black)
    c.setFillColor(white)
    c.setLineWidth(esp)
    tabua = alt * 0.32
    # Travessas altas e tábuas espaçadas: os vãos entre elas precisam ser pintáveis.
    c.rect(x - 5, y_chao + alt * 0.22, w + 10, tabua * 0.75, stroke=1, fill=1)
    n = max(4, int(w // (tabua * 2.6)))
    passo = w / n
    for i in range(n + 1):
        px = x + i * passo - tabua / 2
        caminho = c.beginPath()
        caminho.moveTo(px, y_chao)
        caminho.lineTo(px, y_chao + alt * 0.85)
        caminho.lineTo(px + tabua / 2, y_chao + alt)
        caminho.lineTo(px + tabua, y_chao + alt * 0.85)
        caminho.lineTo(px + tabua, y_chao)
        caminho.close()
        c.drawPath(caminho, stroke=1, fill=1)


def _chao_campo(c, x, y_chao, w, h, chao_h, esp, variante):
    if variante == 0:
        _pedras(c, x, y_chao, w, chao_h, esp)
    elif variante == 1:
        _flor_grande(c, x + w * 0.09, y_chao, h * 0.22, esp)
        _flor_grande(c, x + w * 0.91, y_chao, h * 0.19, esp)
    elif variante == 2:
        _cerca(c, x, y_chao, w, h * 0.17, esp)
    else:
        _arbusto(c, x + w * 0.1, y_chao, w * 0.24, esp)
        _arbusto(c, x + w * 0.9, y_chao, w * 0.2, esp)


# ----------------------------------------------------------------------------- brinquedos e acessórios
def _brinquedo(p: Caneta, nome: str) -> None:
    """Objetos de interação, desenhados na grade 0–100 de um quadrado próprio."""
    if nome == "bola":
        p.circulo(50, 58, 32)
        p.arco(50, 58, 32, 100, 260)
        p.caminho([("M", 22, 44), ("C", 40, 54, 60, 54, 78, 44)], cheio=False, fechar=False)
        p.caminho([("M", 22, 72), ("C", 40, 62, 60, 62, 78, 72)], cheio=False, fechar=False)
    elif nome == "osso":
        for cx in (18, 82):
            p.circulo(cx, 60, 10)
            p.circulo(cx, 80, 10)
        p.retangulo(16, 62, 84, 78, raio=4)
    elif nome == "cenoura":
        for dx in (-8, 0, 8):
            p.elipse(50 + dx, 20, 4, 12, angulo=dx * 2)
        p.poligono([(34, 32), (66, 32), (52, 92), (48, 92)])
        for y in (46, 60, 74):
            p.linha(42 + (y - 46) * 0.12, y, 50, y + 2, espessura=p.espessura_base * 0.7)
    elif nome == "balde":
        p.caminho([("M", 30, 40), ("C", 30, 10, 70, 10, 70, 40)], cheio=False, fechar=False)
        p.poligono([(24, 40), (76, 40), (68, 92), (32, 92)])
        p.retangulo(22, 36, 78, 46, raio=3)
    elif nome == "pipa":
        p.caminho([("M", 50, 90), ("C", 60, 96, 70, 88, 80, 96)], cheio=False, fechar=False)
        p.poligono([(50, 6), (80, 40), (50, 90), (20, 40)])
        p.linha(50, 6, 50, 90)  # só uma divisão: duas metades grandes para pintar
    elif nome == "flor":
        _flor_grande(p.c, p.X(50), p.Y(100), p.s(100), p.espessura_base)
    else:
        raise ValueError(f"Brinquedo '{nome}' não existe. Use: bola, osso, cenoura, balde, "
                         "pipa ou flor.")


# Topo da cabeça de cada figura (x, y, raio aproximado), para acessórios.
CABECA = {
    "gato": (50, 25, 17), "cachorro": (50, 18, 17), "coelho": (50, 30, 15),
    "sapo": (50, 25, 20), "elefante": (26, 28, 14), "dinossauro": (76, 14, 10),
    "coruja": (50, 20, 20), "passarinho": (34, 19, 12), "polvo": (50, 22, 24),
    "pinguim": (50, 28, 20), "tartaruga": (82, 46, 10), "gizinho": (50, 12, 10),
}


def _acessorio(p: Caneta, nome: str, desenho: str) -> None:
    if desenho not in CABECA:
        raise ValueError(f"Acessório não disponível para '{desenho}'. "
                         f"Figuras com cabeça mapeada: {', '.join(sorted(CABECA))}.")
    cx, cy, r = CABECA[desenho]
    if nome == "chapeu":
        p.poligono([(cx - r * 0.6, cy + r * 0.1), (cx + r * 0.6, cy + r * 0.1),
                    (cx + r * 0.05, cy - r * 1.3)])
        p.linha(cx - r * 0.38, cy - r * 0.35, cx + r * 0.42, cy - r * 0.2,
                espessura=p.espessura_base * 0.7)
        p.circulo(cx + r * 0.05, cy - r * 1.42, r * 0.22)
    elif nome == "laco":
        bx = cx + r * 0.55
        p.poligono([(bx, cy), (bx - r * 0.65, cy - r * 0.4), (bx - r * 0.65, cy + r * 0.4)])
        p.poligono([(bx, cy), (bx + r * 0.65, cy - r * 0.4), (bx + r * 0.65, cy + r * 0.4)])
        p.circulo(bx, cy, r * 0.2)
    elif nome == "coroa":
        w = r * 0.8
        p.poligono([(cx - w, cy + r * 0.05), (cx - w, cy - r * 0.6), (cx - w * 0.5, cy - r * 0.25),
                    (cx, cy - r * 0.8), (cx + w * 0.5, cy - r * 0.25), (cx + w, cy - r * 0.6),
                    (cx + w, cy + r * 0.05)])
    else:
        raise ValueError(f"Acessório '{nome}' não existe. Use: chapeu, laco ou coroa.")


def _variante(desenho: str, pag: dict | None, n: int, salto: int = 0) -> int:
    base = pag.get("variacao", 0) if pag else 0
    return (sum(map(ord, desenho)) + base + salto) % n


def desenhar_com_cena(c: Canvas, area: tuple[float, float, float, float], nome: str,
                      cena: str, espessura: float = 3.2, area_min_pt2: float = 0.0,
                      pag: dict | None = None) -> None:
    """Desenha `nome` grande, apoiado no chão, com o cenário ao redor.

    Opções vindas da página do tema (`pag`):
      "variacao": n   muda o céu e o chão sorteados (padrão: depende do desenho)
      "brinquedo":    bola, osso, cenoura, balde, pipa ou flor, ao lado da figura
      "acessorio":    chapeu, laco ou coroa, na cabeça da figura
      "espelhar":     true para virar a figura para o outro lado
    """
    pag = pag or {}
    contorno = pag.get("_contorno", 0)
    x, y, w, h = area
    if cena == "nenhum":
        desenhar(nome, Caneta(c, x, y, w, h, espessura=espessura, area_min_pt2=area_min_pt2),
                 contorno)
        return
    chao_h = h * 0.08
    lado = min(w * 0.94, h - chao_h - h * 0.24)
    if pag.get("brinquedo"):
        lado *= 0.9  # abre espaço ao lado da figura
    y_chao = y + chao_h
    qx = x + (w - lado) / 2
    if pag.get("brinquedo"):
        qx = x + w - lado - w * 0.02
    qy = y_chao - lado * (1 - LINHA_DO_CHAO)
    topo_figura = qy + lado
    faixa_ceu = y + h - topo_figura           # altura livre acima da figura
    esp_cena = espessura * 0.85
    meio_ceu = topo_figura + faixa_ceu / 2

    # O cenário fica recortado dentro da área (não invade a moldura nem a margem).
    c.saveState()
    recorte = c.beginPath()
    recorte.rect(x, y, w, h)
    c.clipPath(recorte, stroke=0, fill=0)

    # --- fundo (atrás da figura) -------------------------------------------------
    if cena == "campo":
        _ceu_campo(c, x, w, meio_ceu, faixa_ceu, esp_cena, _variante(nome, pag, 4))
    elif cena in ("lago", "neve", "mar_superficie"):
        _ceu_campo(c, x, w, meio_ceu, faixa_ceu, esp_cena, _variante(nome, pag, 2))
    if cena == "neve":
        for fx, fy in ((0.08, 0.6), (0.36, 0.25), (0.68, 0.75)):
            _floco(c, x + w * fx, y + h * fy, w * 0.05, esp_cena)
    if cena == "mar":
        c.setStrokeColor(black)
        c.setLineWidth(esp_cena)
        desloc = _variante(nome, pag, 3) * 0.06
        for i, fx in enumerate((0.15, 0.3, 0.7, 0.85)):
            rb = w * (0.035 if i % 2 else 0.05)
            c.setFillColor(white)
            c.circle(x + w * (fx + desloc * (1 if i < 2 else -1)), meio_ceu + (i % 2) * rb,
                     rb, stroke=1, fill=1)
        altura_alga = lado * 0.85
        _alga(c, x + w * 0.07, y_chao - 6, altura_alga, esp_cena)
        _alga(c, x + w * 0.93, y_chao - 6, altura_alga * 0.75, esp_cena)
    elif cena == "noite":
        _lua(c, x + w * 0.82, meio_ceu, min(faixa_ceu * 0.42, w * 0.11), esp_cena)
        for fx, fy in ((0.12, 0.88), (0.4, 0.8), (0.6, 0.93)):
            _estrela_espaco(c, x + w * fx, y + h * fy, w * 0.11, esp_cena)
    elif cena == "espaco":
        _planeta(c, x + w * 0.22, meio_ceu, min(faixa_ceu * 0.38, w * 0.1), esp_cena)
        _lua(c, x + w * 0.8, meio_ceu, min(faixa_ceu * 0.4, w * 0.1), esp_cena)
        for fx, fy in ((0.5, 0.9), (0.1, 0.38), (0.9, 0.55)):
            _estrela_espaco(c, x + w * fx, y + h * fy, w * 0.19, esp_cena)

    # --- chão ------------------------------------------------------------------------
    if cena == "campo":
        variante_chao = _variante(nome, pag, 4, salto=1)
        if nome in FIGURAS_LARGAS:
            variante_chao = 0
        if variante_chao == 2:
            _cerca(c, x, y_chao, w, h * 0.17, esp_cena)  # cerca fica atrás do chão
        # Chão reto: ondulado deixava frestas minúsculas sob objetos de base reta.
        _chao_ondulado(c, x, y_chao, w, esp_cena, amplitude=0)
        if variante_chao != 2:  # tufos dentro da cerca criariam frestas minúsculas
            _tufos(c, x, y_chao, w, esp_cena)
        if variante_chao != 2:
            _chao_campo(c, x, y_chao, w, h, chao_h, esp_cena, variante_chao)
    elif cena in ("lago", "mar_superficie"):
        _chao_ondulado(c, x, y_chao, w, esp_cena, amplitude=7)
        _chao_ondulado(c, x, y_chao - chao_h * 0.5, w, esp_cena, amplitude=7)
    elif cena == "neve":
        _chao_ondulado(c, x, y_chao, w, esp_cena, amplitude=12)  # montinhos de neve
    elif cena == "noite":
        _chao_ondulado(c, x, y_chao, w, esp_cena, amplitude=0)
        _tufos(c, x, y_chao, w, esp_cena)
    elif cena == "mar":
        _chao_ondulado(c, x, y_chao, w, esp_cena, amplitude=5)
        _concha(c, x + w * 0.2, y_chao - chao_h * 0.45, chao_h * 1.5, esp_cena)
        _concha(c, x + w * 0.8, y_chao - chao_h * 0.45, chao_h * 1.3, esp_cena)

    c.restoreState()

    # --- figura --------------------------------------------------------------------
    c.saveState()
    if pag.get("espelhar"):
        eixo = qx + lado / 2
        c.translate(eixo, 0)
        c.scale(-1, 1)
        c.translate(-eixo, 0)
    p = Caneta(c, qx, qy, lado, lado, espessura=espessura, area_min_pt2=area_min_pt2)
    p.sem_chao = cena in ("campo", "lago", "neve", "noite")  # o cenário já desenhou o chão
    desenhar(nome, p, contorno)
    if pag.get("acessorio"):
        sil = copy.copy(p)
        sil.silhueta = espessura * contorno if contorno else None
        if sil.silhueta:
            _acessorio(sil, pag["acessorio"], nome)
        _acessorio(p, pag["acessorio"], nome)
    c.restoreState()

    # --- brinquedo, na frente, ao lado da figura -----------------------------------
    if pag.get("brinquedo"):
        tam = w * 0.25
        # A base dos brinquedos fica perto de y=92 na grade: apoiada na linha do chão.
        bp = Caneta(c, x + w * 0.01, y_chao - tam * 0.08, tam, tam, espessura=espessura,
                    area_min_pt2=area_min_pt2)
        if contorno:
            sil = copy.copy(bp)
            sil.silhueta = espessura * contorno
            _brinquedo(sil, pag["brinquedo"])
        _brinquedo(bp, pag["brinquedo"])
