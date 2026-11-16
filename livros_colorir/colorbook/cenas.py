"""Cenários: transformam a figura solta numa página inteira para pintar.

A figura é desenhada grande e "apoiada no chão"; o espaço que sobra em cima vira
céu (ou água, ou espaço) com elementos grandes e fáceis de pintar. Assim a
página não fica com metade em branco.

Ative no tema com  "cenarios": true. Cada desenho tem um cenário padrão
(CENA_PADRAO); dá para trocar por página com  "cena": "mar"  ou  "cena": "nenhum".
"""
from __future__ import annotations

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
    **dict.fromkeys(["foguete", "estrela"], "espaco"),
    # Desenhos que já ocupam a página sozinhos ficam sem cenário.
    **dict.fromkeys(["sol", "arco_iris", "coracao"], "nenhum"),
}
CENAS = {"campo", "mar", "mar_superficie", "lago", "neve", "espaco", "nenhum"}

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
    p = _quadro(c, cx, cy, tam, esp)
    p.caminho([("M", 10, 80), ("C", 10, 20, 90, 20, 90, 80), ("L", 10, 80)])
    for x in (30, 50, 70):
        p.linha(50, 78, x, 34)


def _estrela_espaco(c, cx, cy, tam, esp):
    _quadro(c, cx, cy, tam, esp).estrela(50, 50, 45, 21)


def _planeta(c, cx, cy, r, esp):
    p = _quadro(c, cx, cy, r * 2.6, esp)
    p.elipse(50, 52, 48, 10, angulo=-15, cheio=False)
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


def desenhar_com_cena(c: Canvas, area: tuple[float, float, float, float], nome: str,
                      cena: str, espessura: float = 3.2, area_min_pt2: float = 0.0) -> None:
    """Desenha `nome` grande, apoiado no chão, com o cenário ao redor."""
    x, y, w, h = area
    if cena == "nenhum":
        desenhar(nome, Caneta(c, x, y, w, h, espessura=espessura, area_min_pt2=area_min_pt2))
        return
    chao_h = h * 0.08
    lado = min(w * 0.94, h - chao_h - h * 0.24)
    y_chao = y + chao_h
    qx = x + (w - lado) / 2
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
    if cena in ("campo", "lago", "neve", "mar_superficie"):
        r_sol = min(faixa_ceu * 0.5, w * 0.14)
        _sol(c, x + w - r_sol * 1.25, meio_ceu, r_sol, esp_cena)
        tam_nuvem = min(faixa_ceu * 1.25, w * 0.4)
        for fx in (0.2, 0.55):
            _nuvem(_quadro(c, x + w * fx, meio_ceu, tam_nuvem, esp_cena), 50, 50, 1.9)
    if cena == "neve":
        for fx, fy in ((0.08, 0.6), (0.36, 0.25), (0.68, 0.75)):
            _floco(c, x + w * fx, y + h * fy, w * 0.05, esp_cena)
    if cena in ("mar", "espaco"):
        if cena == "mar":
            c.setStrokeColor(black)
            c.setLineWidth(esp_cena)
            for i, fx in enumerate((0.15, 0.3, 0.7, 0.85)):
                rb = w * (0.035 if i % 2 else 0.05)
                c.setFillColor(white)
                c.circle(x + w * fx, meio_ceu + (i % 2) * rb, rb, stroke=1, fill=1)
            altura_alga = lado * 0.85
            _alga(c, x + w * 0.07, y_chao - 6, altura_alga, esp_cena)
            _alga(c, x + w * 0.93, y_chao - 6, altura_alga * 0.75, esp_cena)
        else:
            _planeta(c, x + w * 0.22, meio_ceu, min(faixa_ceu * 0.38, w * 0.1), esp_cena)
            _lua(c, x + w * 0.8, meio_ceu, min(faixa_ceu * 0.4, w * 0.1), esp_cena)
            for fx, fy in ((0.5, 0.9), (0.1, 0.35), (0.9, 0.5)):
                _estrela_espaco(c, x + w * fx, y + h * fy, w * 0.14, esp_cena)

    # --- chão ------------------------------------------------------------------------
    if cena == "campo":
        # Chão reto: ondulado deixava frestas minúsculas sob objetos de base reta.
        _chao_ondulado(c, x, y_chao, w, esp_cena, amplitude=0)
        _tufos(c, x, y_chao, w, esp_cena)
        _pedras(c, x, y_chao, w, chao_h, esp_cena)
    elif cena in ("lago", "mar_superficie"):
        _chao_ondulado(c, x, y_chao, w, esp_cena, amplitude=7)
        _chao_ondulado(c, x, y_chao - chao_h * 0.5, w, esp_cena, amplitude=7)
    elif cena == "neve":
        _chao_ondulado(c, x, y_chao, w, esp_cena, amplitude=12)  # montinhos de neve
    elif cena == "mar":
        _chao_ondulado(c, x, y_chao, w, esp_cena, amplitude=5)
        _concha(c, x + w * 0.2, y_chao - chao_h * 0.45, chao_h * 1.5, esp_cena)
        _concha(c, x + w * 0.8, y_chao - chao_h * 0.45, chao_h * 1.3, esp_cena)

    c.restoreState()

    # --- figura --------------------------------------------------------------------
    p = Caneta(c, qx, qy, lado, lado, espessura=espessura, area_min_pt2=area_min_pt2)
    p.sem_chao = cena in ("campo", "lago", "neve")  # o cenário já desenhou o chão
    desenhar(nome, p)
