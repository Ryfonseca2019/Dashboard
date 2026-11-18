"""Folha de teste de impressão: imprima em casa e confira também na cópia de prova.

    python -m colorbook folha-teste

O que você descobre com ela (anote na própria folha e ajuste colorbook/estilo.py):
  - qual o traço mais fino que ainda aparece bem no papel;
  - qual a menor área que a criança consegue pintar sem sair muito da linha;
  - qual tom de cinza do pontilhado ("cubra") fica visível sem parecer traço final;
  - se canetinha, giz de cera e lápis de cor atravessam o papel.
"""
from __future__ import annotations

import math
from pathlib import Path

from reportlab.lib.colors import Color, black
from reportlab.pdfgen.canvas import Canvas

from . import specs
from .caneta import Caneta
from .estilo import PERFIS
from .fonts import FONTE, FONTE_NEGRITO

P = specs.POL
PT_POR_CM = 72 / 2.54


def gerar_folha_teste(saida: Path) -> Path:
    largura, altura = specs.formato("8.5x11")
    W, H = largura * P, altura * P
    c = Canvas(str(saida), pagesize=(W, H), initialFontName=FONTE)
    c.setTitle("Folha de teste de impressão")
    m = 0.6 * P
    y = H - m

    def titulo(texto, tam=13):
        nonlocal y
        c.setFillColor(black)
        c.setFont(FONTE_NEGRITO, tam)
        c.drawString(m, y, texto)
        y -= tam + 8

    c.setFont(FONTE_NEGRITO, 22)
    c.drawString(m, y - 8, "Folha de teste de impressão")
    c.setFont(FONTE, 10)
    c.drawString(m, y - 26, "Imprima no papel do livro (ou confira na cópia de prova do KDP) "
                 "e marque o que observar.")
    y -= 58

    # 1. Escada de espessuras --------------------------------------------------------
    titulo("1. Espessura do traço — marque o mais fino que ainda aparece bem")
    for esp in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0):
        c.setLineWidth(esp)
        c.setStrokeColor(black)
        c.line(m + 70, y + 4, m + 330, y + 4)
        c.setFont(FONTE, 10)
        c.drawString(m, y, f"{esp:g} pt")
        c.setLineWidth(1)
        c.rect(m + 345, y - 2, 11, 11, stroke=1, fill=0)
        y -= 20
    atual = PERFIS["pequenos"].traco_min_pt, PERFIS["maiores"].traco_min_pt
    c.setFont(FONTE, 9)
    c.drawString(m, y, f"Mínimo atual: {atual[0]} pt (2 a 5 anos), {atual[1]} pt (5 a 10 anos).")
    y -= 28

    # 2. Áreas para pintar -----------------------------------------------------------
    titulo("2. Tamanho das áreas — a criança pinta cada círculo sem sair da linha")
    areas = (0.2, 0.4, 0.8, 1.5, 3.0, 5.0)
    x = m + 10
    maior_r = math.sqrt(areas[-1] / math.pi) * PT_POR_CM
    base = y - maior_r - 4
    for a in areas:
        r = math.sqrt(a / math.pi) * PT_POR_CM
        c.setLineWidth(2.5)
        c.circle(x + r, base, r, stroke=1, fill=0)
        c.setFont(FONTE, 10)
        c.drawCentredString(x + r, base - maior_r - 16, f"{a:g} cm²")
        c.setLineWidth(1)
        c.rect(x + r - 5, base - maior_r - 34, 10, 10, stroke=1, fill=0)
        x += 2 * r + 34
    y = base - maior_r - 52
    atual = PERFIS["pequenos"].area_min_cm2, PERFIS["maiores"].area_min_cm2
    c.setFont(FONTE, 9)
    c.drawString(m, y, f"Mínimo atual: {atual[0]} cm² (2 a 5 anos), {atual[1]} cm² (5 a 10 anos). "
                 "Marque o menor que deu para pintar bem.")
    y -= 28

    # 3. Pontilhado -------------------------------------------------------------------
    titulo("3. Pontilhado para cobrir — qual tom aparece sem parecer traço final?")
    x = m
    for cinza in (0.35, 0.55, 0.7):
        lado = 90
        p = Caneta(c, x, y - lado, lado, lado, espessura=2.4, cor_traco=Color(cinza, cinza, cinza),
                   tracejado=(5, 5))
        p.estrela(50, 50, 46, 22)
        c.setDash()
        c.setFillColor(black)
        c.setStrokeColor(black)
        c.setLineWidth(1)
        c.setFont(FONTE, 10)
        c.drawCentredString(x + lado / 2, y - lado - 14, f"cinza {int(cinza * 100)}%")
        c.rect(x + lado / 2 - 5, y - lado - 32, 10, 10, stroke=1, fill=0)
        x += lado + 50
    y -= 136

    # 4. Materiais --------------------------------------------------------------------
    titulo("4. Materiais — pinte cada quadrado e olhe o verso da folha")
    materiais = ("Giz de cera", "Lápis de cor", "Canetinha", "Marcador grosso")
    lado = 56
    x = m
    for mat in materiais:
        c.setStrokeColor(black)
        c.setLineWidth(2.5)
        c.roundRect(x, y - lado, lado * 1.6, lado, 10, stroke=1, fill=0)
        c.setFont(FONTE_NEGRITO, 10)
        c.drawString(x, y - lado - 14, mat)
        c.setFont(FONTE, 9)
        c.drawString(x, y - lado - 28, "Atravessou o papel?")
        c.drawString(x, y - lado - 41, "sim ☐   não ☐")
        x += lado * 1.6 + 16
    c.setFont(FONTE, 8)
    c.drawString(m, 0.45 * P, "Gerado por colorbook · leve esta folha junto com a cópia de prova "
                 "e use as respostas para ajustar as regras de estilo.")
    c.showPage()
    c.save()
    return saida
