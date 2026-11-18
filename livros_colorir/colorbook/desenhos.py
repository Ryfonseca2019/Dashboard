"""Biblioteca de desenhos em traço, escritos à mão em código.

Cada desenho é uma função que recebe uma `Caneta` e desenha numa grade
0–100 (Y para baixo). Para criar um desenho novo, basta escrever uma função
com o decorador `@desenho("nome")`; ele já fica disponível nos temas.

Dicas para desenhos infantis (2 a 6 anos):
- áreas grandes, poucas linhas e contorno grosso;
- desenhe primeiro o que fica "atrás" (as formas de cima tampam as de baixo);
- olhos como bolinhas pretas, sorrisos simples.
"""
from __future__ import annotations

import copy
import math
from typing import Callable

from .caneta import Caneta

DESENHOS: dict[str, Callable[[Caneta], None]] = {}


def desenho(nome: str):
    def registrar(func):
        DESENHOS[nome] = func
        return func
    return registrar


def desenhar(nome: str, caneta: Caneta, contorno: float = 0.0) -> None:
    """Desenha pelo nome. Também aceita "mandala:SEMENTE" (ex.: "mandala:104").

    contorno: se > 0, desenha antes a silhueta da figura em preto com traço
    `contorno` vezes mais grosso. O desenho normal por cima deixa à mostra só a
    borda de fora: contorno externo grosso e detalhes internos finos, como fazem
    os ilustradores."""
    if contorno:
        silhueta = copy.copy(caneta)
        silhueta.silhueta = caneta.espessura_base * contorno
        _desenhar(nome, silhueta)
        caneta.fator_area = max(caneta.fator_area, 1.8)
    _desenhar(nome, caneta)


def _desenhar(nome: str, caneta: Caneta) -> None:
    if nome.startswith("mandala"):
        from .mandalas import mandala

        _, _, semente = nome.partition(":")
        mandala(caneta, semente=int(semente or 1), nivel=1)
        return
    try:
        DESENHOS[nome](caneta)
    except KeyError as exc:
        raise ValueError(
            f"Desenho '{nome}' não existe. Disponíveis: {', '.join(sorted(DESENHOS))}"
        ) from exc


def _rosto(p: Caneta, cx, cy, abertura=7, olho=1.8, sorriso=6, dy_boca=6):
    p.ponto(cx - abertura, cy, olho)
    p.ponto(cx + abertura, cy, olho)
    p.sorriso(cx, cy + dy_boca - sorriso * 0.6, sorriso)


def _bochecha(p: Caneta, cx, cy):
    """Rubor nas bochechas em três risquinhos (não forma área pequena para pintar)."""
    for i in (-1, 0, 1):
        p.linha(cx + i * 1.9 - 0.8, cy + 1.3, cx + i * 1.9 + 0.8, cy - 1.3, espessura=1.8)


def _nuvem(p: Caneta, cx, cy, escala=1.0):
    e = escala
    p.caminho([
        ("M", cx - 16 * e, cy + 6 * e),
        ("C", cx - 24 * e, cy + 6 * e, cx - 24 * e, cy - 6 * e, cx - 14 * e, cy - 5 * e),
        ("C", cx - 14 * e, cy - 14 * e, cx - 2 * e, cy - 16 * e, cx + 2 * e, cy - 9 * e),
        ("C", cx + 6 * e, cy - 16 * e, cx + 20 * e, cy - 12 * e, cx + 16 * e, cy - 3 * e),
        ("C", cx + 25 * e, cy - 2 * e, cx + 24 * e, cy + 7 * e, cx + 16 * e, cy + 6 * e),
    ])


def _grama(p: Caneta, y=90):
    if getattr(p, "sem_chao", False):  # o cenário da página já desenhou o chão
        return
    p.linha(5, y, 95, y)
    for x in range(10, 95, 12):
        p.polilinha([(x, y), (x + 2, y - 5), (x + 4, y)])


# ----------------------------------------------------------------------------- natureza
@desenho("sol")
def sol(p: Caneta):
    for i in range(12):
        a = math.radians(i * 30)
        b1 = math.radians(i * 30 - 9)
        b2 = math.radians(i * 30 + 9)
        p.poligono([
            (50 + 27 * math.cos(b1), 50 + 27 * math.sin(b1)),
            (50 + 44 * math.cos(a), 50 + 44 * math.sin(a)),
            (50 + 27 * math.cos(b2), 50 + 27 * math.sin(b2)),
        ])
    p.circulo(50, 50, 28)
    p.circulo(39, 57, 4.5)  # bochechas
    p.circulo(61, 57, 4.5)
    _rosto(p, 50, 45, abertura=8, olho=2.6, sorriso=10, dy_boca=12)


@desenho("arvore")
def arvore(p: Caneta):
    _grama(p, 92)
    p.poligono([(44, 92), (46, 55), (54, 55), (56, 92)])
    p.circulo(32, 46, 17)
    p.circulo(68, 46, 17)
    p.circulo(50, 30, 22)
    p.circulo(50, 50, 16)
    for x, y in ((38, 30), (60, 26), (30, 50), (70, 50), (52, 45)):
        p.circulo(x, y, 5.5)  # frutinhas (grandes o bastante para pintar)


@desenho("flor")
def flor(p: Caneta):
    p.tubo([("M", 50, 92), ("C", 48, 75, 54, 60, 50, 45)], largura=5)
    p.caminho([("M", 50, 75), ("C", 60, 62, 76, 64, 80, 66), ("C", 72, 78, 58, 80, 50, 75)])
    p.caminho([("M", 50, 82), ("C", 40, 70, 24, 72, 20, 74), ("C", 28, 86, 42, 88, 50, 82)])
    for i in range(8):
        a = i * 45
        r = math.radians(a)
        p.elipse(50 + 15 * math.cos(r), 32 + 15 * math.sin(r), 11, 7, angulo=a)
    p.circulo(50, 32, 11)
    _rosto(p, 50, 30, abertura=4, olho=1.4, sorriso=4, dy_boca=6)


@desenho("arco_iris")
def arco_iris(p: Caneta):
    for r in (40, 33, 26, 19):
        p.caminho([("M", 50 - r, 70), ("C", 50 - r, 70 - r * 1.33, 50 + r, 70 - r * 1.33,
                                        50 + r, 70)])
    p.caminho([("M", 38, 70), ("C", 38, 54, 62, 54, 62, 70)])
    _nuvem(p, 18, 70, 0.9)
    _nuvem(p, 82, 70, 0.9)
    p.estrela(50, 18, 5)
    p.estrela(22, 28, 3.5)
    p.estrela(78, 28, 3.5)


@desenho("estrela")
def estrela(p: Caneta):
    p.estrela(50, 54, 44, 20)
    _bochecha(p, 40, 62)
    _bochecha(p, 60, 62)
    _rosto(p, 50, 55, abertura=7, olho=2.4, sorriso=7, dy_boca=9)
    p.estrela(14, 14, 5)
    p.estrela(86, 18, 4)


# ----------------------------------------------------------------------------- animais
@desenho("gato")
def gato(p: Caneta):
    p.tubo([("M", 66, 84), ("C", 92, 82, 90, 56, 80, 50)], largura=7)
    p.elipse(50, 70, 22, 20)
    p.elipse(42, 88, 7, 4)
    p.elipse(58, 88, 7, 4)
    p.poligono([(34, 32), (33, 12), (48, 24)])
    p.poligono([(66, 32), (67, 12), (52, 24)])
    p.elipse(50, 40, 20, 17)
    p.ponto(42, 37, 2.4)
    p.ponto(58, 37, 2.4)
    p.poligono([(47, 43), (53, 43), (50, 46)])
    p.arco(47, 47, 3, 200, 360, espessura=2)
    p.arco(53, 47, 3, 180, 340, espessura=2)
    for dy in (-2, 2):
        p.linha(38, 45 + dy, 24, 43 + dy * 2, espessura=1.8)
        p.linha(62, 45 + dy, 76, 43 + dy * 2, espessura=1.8)


@desenho("peixe")
def peixe(p: Caneta):
    p.poligono([(68, 50), (90, 30), (86, 50), (90, 70)])
    p.caminho([("M", 40, 33), ("C", 44, 20, 56, 20, 60, 34)])
    p.elipse(45, 50, 28, 19)
    p.arco(56, 50, 14, 125, 235, espessura=2.5)  # guelra
    for x, y in ((44, 46), (36, 54), (46, 58)):
        p.arco(x, y, 4, 200, 340, espessura=2)  # escamas
    p.circulo(28, 46, 4.5)
    p.ponto(27, 46, 2)
    p.arco(22, 56, 3, 200, 340, espessura=2)
    p.circulo(16, 30, 6)    # bolhas
    p.circulo(8, 15, 4.5)
    p.caminho([("M", 5, 92), ("C", 20, 82, 30, 82, 40, 92), ("L", 5, 92)])
    p.caminho([("M", 60, 92), ("C", 70, 78, 78, 78, 84, 92), ("L", 60, 92)])


@desenho("borboleta")
def borboleta(p: Caneta):
    p.elipse(30, 36, 22, 17, angulo=-30)
    p.elipse(70, 36, 22, 17, angulo=30)
    p.elipse(34, 66, 15, 12, angulo=30)
    p.elipse(66, 66, 15, 12, angulo=-30)
    for x, y, r in ((28, 34, 7), (72, 34, 7), (33, 67, 4.5), (67, 67, 4.5)):
        p.circulo(x, y, r)
    p.elipse(50, 52, 5, 26)
    p.circulo(50, 24, 6)
    p.ponto(48, 23, 1.2)
    p.ponto(52, 23, 1.2)
    p.caminho([("M", 48, 19), ("C", 44, 10, 38, 8, 34, 9)], fechar=False)
    p.caminho([("M", 52, 19), ("C", 56, 10, 62, 8, 66, 9)], fechar=False)
    p.circulo(34, 9, 2.5)
    p.circulo(66, 9, 2.5)


@desenho("tartaruga")
def tartaruga(p: Caneta):
    for x in (28, 66):
        p.elipse(x, 72, 8, 6)
    p.poligono([(16, 64), (6, 68), (16, 70)])
    p.elipse(82, 56, 11, 10)
    p.ponto(85, 53, 2)
    p.arco(84, 59, 4, 200, 330, espessura=2)
    p.caminho([("M", 14, 68), ("C", 14, 30, 74, 30, 74, 68), ("L", 14, 68)])
    p.poligono([(36, 46), (52, 46), (58, 58), (44, 64), (30, 58)], cheio=False, espessura=2.5)
    for a, b in (((36, 46), (30, 38)), ((52, 46), (58, 38)), ((58, 58), (72, 60)),
                 ((44, 64), (44, 68)), ((30, 58), (16, 60))):
        p.linha(*a, *b, espessura=2.5)
    p.linha(8, 68, 92, 68, espessura=2.5)
    _grama(p, 88)


@desenho("passarinho")
def passarinho(p: Caneta):
    p.tubo([("M", 8, 76), ("C", 40, 72, 70, 78, 94, 72)], largura=6)
    p.caminho([("M", 74, 42), ("L", 92, 30), ("L", 90, 50), ("L", 74, 52)])
    p.elipse(52, 50, 24, 20)
    p.circulo(34, 32, 13)
    p.poligono([(22, 30), (12, 34), (22, 37)])
    p.ponto(31, 30, 2.2)
    p.caminho([("M", 46, 46), ("C", 56, 36, 72, 42, 70, 52), ("C", 64, 60, 50, 58, 46, 46)])
    for x in (46, 58):
        p.linha(x, 69, x, 75, espessura=2.5)  # perninhas (pés em "v" fechavam áreas mínimas)
    p.circulo(80, 16, 6)
    p.circulo(88, 22, 4)


@desenho("coruja")
def coruja(p: Caneta):
    p.tubo([("M", 6, 86), ("L", 94, 86)], largura=6)
    p.poligono([(30, 22), (26, 6), (42, 16)])
    p.poligono([(70, 22), (74, 6), (58, 16)])
    p.elipse(50, 52, 30, 36)
    p.caminho([("M", 22, 46), ("C", 8, 60, 14, 76, 26, 80), ("C", 28, 66, 28, 56, 22, 46)])
    p.caminho([("M", 78, 46), ("C", 92, 60, 86, 76, 74, 80), ("C", 72, 66, 72, 56, 78, 46)])
    p.elipse(50, 64, 16, 18)
    for y in (58, 66, 74):
        for x in (44, 56):
            p.arco(x, y, 4, 200, 340, espessura=2)
    for x in (37, 63):
        p.circulo(x, 34, 12)
        p.circulo(x, 34, 6)
        p.ponto(x, 34, 2.6)
    p.poligono([(46, 44), (54, 44), (50, 52)])
    for x in (42, 58):
        p.elipse(x, 86, 5, 3)


# ----------------------------------------------------------------------------- objetos
@desenho("casa")
def casa(p: Caneta):
    _grama(p, 88)
    p.retangulo(62, 18, 72, 40)
    p.retangulo(24, 48, 76, 88)
    p.poligono([(16, 50), (50, 18), (84, 50)])
    p.retangulo(43, 62, 57, 88, raio=2)
    p.ponto(54, 76, 1.4)
    for x in (27, 61):
        p.retangulo(x, 55, x + 12, 67, raio=1.5)
    p.circulo(50, 36, 5)
    _nuvem(p, 22, 14, 0.6)


@desenho("carro")
def carro(p: Caneta):
    p.linha(4, 82, 96, 82)
    p.caminho([("M", 30, 50), ("L", 38, 32), ("L", 64, 32), ("L", 74, 50)])
    p.retangulo(12, 48, 88, 72, raio=7)
    p.poligono([(36, 48), (41, 36), (50, 36), (50, 48)])
    p.poligono([(54, 48), (54, 36), (62, 36), (68, 48)])
    p.retangulo(82, 54, 88, 60, raio=1.5)
    p.retangulo(12, 54, 17, 60, raio=1.5)
    p.linha(46, 56, 52, 56, espessura=2.5)
    for x in (30, 70):
        p.circulo(x, 72, 10)
        p.circulo(x, 72, 4)


@desenho("foguete")
def foguete(p: Caneta):
    p.caminho([("M", 42, 78), ("C", 40, 88, 46, 94, 50, 98), ("C", 54, 94, 60, 88, 58, 78)])
    p.poligono([(38, 60), (24, 80), (40, 78)])
    p.poligono([(62, 60), (76, 80), (60, 78)])
    p.caminho([("M", 50, 6), ("C", 66, 20, 64, 50, 60, 80), ("L", 40, 80),
               ("C", 36, 50, 34, 20, 50, 6)])
    p.caminho([("M", 42, 22), ("C", 46, 16, 54, 16, 58, 22)], cheio=False, fechar=False)
    p.circulo(50, 40, 8)
    p.circulo(50, 40, 5)
    p.retangulo(46, 78, 54, 84)
    for x, y, r in ((14, 16, 5), (84, 30, 4), (18, 50, 3.5), (86, 70, 5)):
        p.estrela(x, y, r)
    p.circulo(80, 10, 4)


@desenho("barco")
def barco(p: Caneta):
    p.circulo(82, 16, 8)
    p.linha(50, 14, 50, 66)
    p.poligono([(52, 16), (52, 60), (82, 60)])
    p.poligono([(48, 24), (48, 60), (24, 60)])
    p.poligono([(50, 14), (64, 18), (50, 22)])
    p.poligono([(16, 64), (84, 64), (74, 80), (26, 80)])
    for x in (36, 50, 64):
        p.circulo(x, 71, 3)
    p.caminho([("M", 4, 84), ("C", 12, 78, 20, 78, 28, 84), ("C", 36, 78, 44, 78, 52, 84),
               ("C", 60, 78, 68, 78, 76, 84), ("C", 84, 78, 92, 78, 96, 84), ("L", 96, 96),
               ("L", 4, 96)])


@desenho("baloes")
def baloes(p: Caneta):
    for (x, y), (fx, fy) in (((30, 30), (46, 88)), ((70, 28), (52, 88)), ((50, 44), (50, 88))):
        p.caminho([("M", x, y + 18), ("C", x + 4, y + 30, fx - 6, fy - 20, fx, fy)],
                  fechar=False, espessura=2)
    for x, y in ((30, 30), (70, 28), (50, 44)):
        p.elipse(x, y, 15, 18)
        p.poligono([(x - 3, y + 21), (x + 3, y + 21), (x, y + 17)])
        p.arco(x - 5, y - 6, 6, 110, 170, espessura=2)
    p.retangulo(44, 86, 56, 94, raio=2)


@desenho("sorvete")
def sorvete(p: Caneta):
    p.poligono([(30, 52), (70, 52), (50, 96)])
    for i in range(1, 4):
        p.linha(30 + i * 7, 52, 50 + i * 2.5, 96 - i * 9, espessura=2)
        p.linha(70 - i * 7, 52, 50 - i * 2.5, 96 - i * 9, espessura=2)
    p.circulo(38, 46, 13)
    p.circulo(62, 46, 13)
    p.circulo(50, 30, 15)
    p.caminho([("M", 26, 52), ("C", 30, 60, 34, 52, 38, 58), ("C", 42, 52, 46, 60, 50, 56),
               ("C", 54, 60, 58, 52, 62, 58), ("C", 66, 52, 70, 60, 74, 52),
               ("C", 72, 46, 28, 46, 26, 52)])
    p.circulo(50, 12, 5)
    p.caminho([("M", 51, 7), ("C", 53, 2, 58, 2, 60, 3)], fechar=False, espessura=2.5)
    for x, y in ((44, 26), (56, 32), (36, 44), (64, 42)):
        p.retangulo(x - 2, y - 1, x + 2, y + 1, raio=1, espessura=2)


@desenho("maca")
def maca(p: Caneta):
    p.tubo([("M", 50, 26), ("C", 50, 18, 52, 12, 56, 8)], largura=4)
    p.caminho([("M", 54, 18), ("C", 60, 6, 74, 6, 80, 10), ("C", 74, 20, 62, 22, 54, 18)])
    p.caminho([("M", 50, 26), ("C", 40, 16, 14, 18, 14, 46), ("C", 14, 72, 32, 94, 50, 86),
               ("C", 68, 94, 86, 72, 86, 46), ("C", 86, 18, 60, 16, 50, 26)])
    p.arco(28, 42, 8, 110, 170, espessura=2.5)
    _rosto(p, 50, 52, abertura=9, olho=2.4, sorriso=8, dy_boca=10)


@desenho("coracao")
def coracao(p: Caneta):
    p.caminho([("M", 50, 30), ("C", 40, 10, 8, 14, 10, 42), ("C", 12, 62, 36, 76, 50, 90),
               ("C", 64, 76, 88, 62, 90, 42), ("C", 92, 14, 60, 10, 50, 30)])
    p.caminho([("M", 50, 42), ("C", 45, 32, 30, 34, 31, 47), ("C", 32, 56, 43, 63, 50, 70),
               ("C", 57, 63, 68, 56, 69, 47), ("C", 70, 34, 55, 32, 50, 42)])
    for x, y in ((14, 10), (86, 10), (10, 84), (90, 84)):
        p.estrela(x, y, 4)


# ----------------------------------------------------------------------------- mais animais
@desenho("cachorro")
def cachorro(p: Caneta):
    p.tubo([("M", 68, 76), ("C", 80, 74, 86, 64, 86, 54)], largura=6)
    p.elipse(50, 72, 22, 18)
    p.circulo(60, 70, 6)
    p.elipse(41, 89, 8, 4)
    p.elipse(59, 89, 8, 4)
    p.retangulo(36, 54, 64, 60, raio=3)
    p.circulo(50, 62, 3)
    p.circulo(50, 36, 19)
    p.elipse(50, 45, 10, 7.5)
    p.elipse(50, 41, 4, 2.8, cheio=p.cor_traco)
    p.arco(47, 46, 3, 200, 360, espessura=2)
    p.arco(53, 46, 3, 180, 340, espessura=2)
    p.ponto(42, 32, 2.4)
    p.ponto(58, 32, 2.4)
    p.elipse(30, 38, 7, 15, angulo=18)
    p.elipse(70, 38, 7, 15, angulo=-18)


@desenho("coelho")
def coelho(p: Caneta):
    for x, a in ((41, -8), (59, 8)):
        p.elipse(x, 18, 6.5, 17, angulo=a)
        p.elipse(x, 19, 3, 11, angulo=a, espessura=2)
    p.circulo(71, 78, 6)
    p.elipse(50, 72, 20, 19)
    p.elipse(50, 75, 11, 12)
    p.elipse(38, 90, 9, 4)
    p.elipse(62, 90, 9, 4)
    p.elipse(39, 64, 4, 7, angulo=25)
    p.elipse(61, 64, 4, 7, angulo=-25)
    p.circulo(50, 44, 17)
    _bochecha(p, 40, 49)
    _bochecha(p, 60, 49)
    p.ponto(44, 41, 2.3)
    p.ponto(56, 41, 2.3)
    p.poligono([(47.5, 46), (52.5, 46), (50, 49)])
    p.arco(48, 50, 2.5, 200, 360, espessura=2)
    p.arco(52, 50, 2.5, 180, 340, espessura=2)


@desenho("elefante")
def elefante(p: Caneta):
    for x1 in (32, 46, 62, 76):
        p.retangulo(x1, 68, x1 + 10, 90, raio=3)
    p.polilinha([(84, 56), (92, 66)], espessura=2.5)
    p.elipse(93, 69, 2.5, 4, cheio=True)
    p.elipse(56, 58, 30, 22)
    p.tubo([("M", 20, 50), ("C", 8, 60, 8, 74, 16, 80)], largura=7)
    p.circulo(28, 42, 16)
    p.elipse(39, 44, 10, 13)
    p.ponto(22, 38, 2.3)
    p.arco(24, 50, 4, 200, 320, espessura=2)
    _grama(p, 90)


@desenho("dinossauro")
def dinossauro(p: Caneta):
    _grama(p, 90)
    p.caminho([("M", 32, 62), ("C", 20, 64, 10, 60, 4, 50), ("C", 12, 70, 24, 78, 36, 76)])
    for x in (38, 46, 54):
        p.poligono([(x - 4, 58), (x, 46), (x + 4, 58)])
    p.retangulo(34, 70, 44, 90, raio=3)
    p.retangulo(56, 70, 66, 90, raio=3)
    p.caminho([("M", 58, 60), ("C", 62, 42, 64, 32, 70, 26), ("L", 78, 30),
               ("C", 74, 38, 72, 50, 70, 64)])
    p.elipse(50, 66, 21, 14)
    p.elipse(76, 22, 12, 8)
    p.ponto(79, 19, 2)
    p.arco(80, 22, 4, 220, 320, espessura=2)
    p.circulo(41, 65, 4.8)  # manchas
    p.circulo(54, 69, 5.2)


@desenho("pinguim")
def pinguim(p: Caneta):
    p.elipse(42, 90, 8, 3.5)
    p.elipse(58, 90, 8, 3.5)
    p.elipse(27, 60, 6, 16, angulo=18)
    p.elipse(73, 60, 6, 16, angulo=-18)
    p.elipse(50, 58, 24, 32)
    p.elipse(50, 64, 16, 23)
    p.ponto(43, 38, 2.4)
    p.ponto(57, 38, 2.4)
    _bochecha(p, 38, 46)
    _bochecha(p, 62, 46)
    p.poligono([(46, 43), (54, 43), (50, 49)])
    # gorro com pompom
    p.caminho([("M", 33, 31), ("C", 34, 14, 66, 14, 67, 31)])
    p.retangulo(30, 28, 70, 34, raio=3)
    p.circulo(50, 14, 4.5)


@desenho("joaninha")
def joaninha(p: Caneta):
    for y in (44, 58, 72):
        p.linha(22, y, 8, y - 4)
        p.linha(78, y, 92, y - 4)
    p.caminho([("M", 46, 18), ("C", 42, 10, 36, 8, 32, 8)], fechar=False)
    p.caminho([("M", 54, 18), ("C", 58, 10, 64, 8, 68, 8)], fechar=False)
    p.circulo(32, 8, 2.5)
    p.circulo(68, 8, 2.5)
    p.circulo(50, 26, 11)
    p.circulo(46, 24, 2.5)
    p.circulo(54, 24, 2.5)
    p.circulo(50, 58, 30)
    p.linha(50, 30, 50, 88)
    for x, y, r in ((38, 44, 5), (62, 44, 5), (33, 62, 6), (67, 62, 6), (42, 77, 5), (58, 77, 5)):
        p.circulo(x, y, r)


@desenho("caracol")
def caracol(p: Caneta):
    p.linha(4, 86, 96, 86)
    p.caminho([("M", 86, 84), ("L", 24, 84), ("C", 14, 84, 12, 74, 16, 68),
               ("C", 12, 56, 16, 46, 26, 46), ("C", 34, 46, 38, 56, 34, 66),
               ("L", 84, 74), ("C", 92, 76, 92, 84, 86, 84)])
    p.linha(22, 48, 16, 32)
    p.linha(30, 48, 32, 32)
    p.circulo(16, 30, 3)
    p.circulo(32, 30, 3)
    p.ponto(22, 55, 1.8)
    p.ponto(30, 55, 1.8)
    p.arco(26, 59, 3.5, 200, 340, espessura=2)
    p.circulo(60, 52, 22)
    pts = []
    for i in range(0, 300):
        t = i / 300 * 3.2 * math.pi
        r = 19 - t * 1.7
        if r < 1:
            break
        pts.append((60 + r * math.cos(t + math.pi), 52 + r * math.sin(t + math.pi)))
    p.polilinha(pts, espessura=2.6)


@desenho("sapo")
def sapo(p: Caneta):
    p.caminho([("M", 50, 92), ("C", 20, 94, 6, 88, 10, 82), ("C", 14, 76, 40, 74, 50, 76),
               ("L", 54, 84), ("L", 60, 76), ("C", 76, 74, 94, 78, 90, 84),
               ("C", 88, 92, 70, 92, 50, 92)])
    p.elipse(26, 80, 13, 7)
    p.elipse(74, 80, 13, 7)
    p.elipse(50, 66, 25, 19)
    p.elipse(50, 70, 14, 11)
    p.elipse(40, 85, 7, 3.5)
    p.elipse(60, 85, 7, 3.5)
    p.elipse(50, 42, 26, 15)
    for x in (35, 65):
        p.circulo(x, 30, 9)
        p.circulo(x, 30, 4.5)
        p.ponto(x, 30, 2.2)
    p.arco(50, 36, 14, 210, 330)
    _bochecha(p, 32, 46)
    _bochecha(p, 68, 46)


@desenho("polvo")
def polvo(p: Caneta):
    for cmd in (
        [("M", 30, 58), ("C", 22, 72, 14, 80, 22, 88)],
        [("M", 38, 60), ("C", 36, 76, 28, 84, 34, 92)],
        [("M", 46, 62), ("C", 46, 78, 42, 86, 46, 94)],
        [("M", 54, 62), ("C", 54, 78, 58, 86, 54, 94)],
        [("M", 62, 60), ("C", 64, 76, 72, 84, 66, 92)],
        [("M", 70, 58), ("C", 78, 72, 86, 80, 78, 88)],
    ):
        p.tubo(cmd, largura=7)
    p.caminho([("M", 20, 60), ("C", 16, 16, 84, 16, 80, 60), ("C", 64, 68, 36, 68, 20, 60)])
    for x in (40, 60):
        p.circulo(x, 44, 6)
        p.ponto(x + 1, 45, 2.5)
    p.arco(50, 50, 6, 210, 330)
    _bochecha(p, 32, 52)
    _bochecha(p, 68, 52)
    p.circulo(46, 28, 3)
    p.circulo(58, 26, 2)
    p.circulo(88, 18, 4)
    p.circulo(82, 8, 2.5)


# ----------------------------------------------------------------------------- mais objetos
@desenho("trem")
def trem(p: Caneta):
    if getattr(p, "sem_chao", False):
        # Com cenário, os dormentes atravessam a linha do chão (sem faixa picotada).
        for x in range(8, 96, 10):
            p.retangulo(x, 88, x + 5, 94, espessura=2)
    else:
        p.linha(4, 88, 96, 88)
        for x in range(8, 96, 10):
            p.retangulo(x, 86, x + 5, 90, espessura=2)
    p.circulo(28, 19, 6)    # fumaça
    p.circulo(39, 11, 7.5)
    p.circulo(51, 6, 5.5)
    p.poligono([(24, 46), (22, 30), (34, 30), (32, 46)])
    p.retangulo(20, 25, 36, 31, raio=1.5)
    p.retangulo(54, 30, 82, 74, raio=2)
    p.retangulo(50, 24, 86, 32, raio=2)
    p.retangulo(16, 46, 56, 74, raio=4)
    p.retangulo(60, 38, 76, 52, raio=1.5)
    p.retangulo(10, 62, 16, 74, raio=1.5)
    p.circulo(22, 54, 3)
    for x, r in ((28, 8), (48, 8), (70, 9)):
        p.circulo(x, 78, r)
        p.circulo(x, 78, 2.5)


# ----------------------------------------------------------------------------- mascote
@desenho("gizinho")
def gizinho(p: Caneta):
    """Gizinho, o giz de cera mascote da coleção."""
    p.tubo([("M", 37, 60), ("C", 28, 58, 22, 50, 20, 42)], largura=5)   # braço acenando
    p.tubo([("M", 63, 60), ("C", 72, 62, 76, 68, 78, 74)], largura=5)   # braço para baixo
    p.circulo(19, 39, 4.5)
    p.circulo(79, 77, 4.5)
    p.elipse(43, 90, 8, 4)
    p.elipse(57, 90, 8, 4)
    p.poligono([(44, 14), (50, 3), (56, 14)])                           # ponta
    p.poligono([(36, 30), (44, 14), (56, 14), (64, 30)])                # cone
    p.retangulo(36, 30, 64, 87, raio=4)                                  # corpo
    p.retangulo(36, 38, 64, 45)                                          # faixas do papel
    p.retangulo(36, 76, 64, 83)
    p.ponto(44, 55, 2.6)
    p.ponto(56, 55, 2.6)
    _bochecha(p, 40, 62)
    _bochecha(p, 60, 62)
    p.sorriso(50, 61, 6)


# ----------------------------------------------------------------------------- poses
@desenho("gato_dormindo")
def gato_dormindo(p: Caneta):
    """Pose alternativa do gato: dormindo enroladinho numa almofada."""
    p.elipse(54, 86, 44, 8)                                            # almofada
    p.tubo([("M", 82, 72), ("C", 96, 80, 88, 92, 62, 88)], largura=6)  # rabo
    p.elipse(56, 70, 31, 17)                                           # corpo
    p.poligono([(15, 58), (14, 42), (27, 51)])                          # orelhas
    p.poligono([(31, 50), (38, 38), (41, 53)])
    p.circulo(28, 62, 15)                                              # cabeça
    p.arco(22, 60, 3.2, 200, 340)                                      # olhos fechados
    p.arco(34, 60, 3.2, 200, 340)
    p.poligono([(26.5, 65), (29.5, 65), (28, 67.5)], cheio=p.cor_traco)
    p.arco(26.5, 68, 1.8, 200, 360, espessura=2)
    p.arco(29.5, 68, 1.8, 180, 340, espessura=2)
    p.elipse(37, 82, 8, 4)                                             # patinha
    for x, y, t in ((46, 36, 5), (55, 27, 6.5), (66, 16, 8)):          # Zzz
        p.polilinha([(x, y), (x + t, y), (x, y + t), (x + t, y + t)],
                    espessura=p.espessura_base * 0.8)
