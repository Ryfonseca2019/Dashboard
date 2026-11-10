"""Mandalas geradas por algoritmo: cada `semente` gera uma mandala diferente,
sempre igual para a mesma semente (dá para reimprimir o mesmo livro).

`nivel` controla a dificuldade: 1 = poucas áreas grandes (crianças pequenas),
3 = muitos detalhes (crianças maiores).

Construção: anéis concêntricos, do maior para o menor. Cada anel é um disco
branco com contorno; os enfeites do anel ficam dentro dele, e o disco do anel
seguinte (menor) tampa o centro. Assim nada fica "solto" na página.
"""
from __future__ import annotations

import math
import random

from .caneta import Caneta

C = 50.0  # centro


def _polar(r, graus):
    a = math.radians(graus)
    return C + r * math.cos(a), C + r * math.sin(a)


def _petalas(p, r_in, r_out, n, giro, cheia=True):
    meio = (r_in + r_out) / 2
    comp = (r_out - r_in) / 2 * 0.9
    larg = min(comp * 0.7, math.pi * meio / n * 0.8)
    for i in range(n):
        a = giro + i * 360 / n
        x, y = _polar(meio, a)
        p.elipse(x, y, comp, larg, angulo=a, cheio=cheia)


def _pontas(p, r_in, r_out, n, giro):
    for i in range(n):
        a = giro + i * 360 / n
        p.poligono([_polar(r_in, a - 180 / n), _polar(r_out * 0.97, a), _polar(r_in, a + 180 / n)])


def _bolinhas(p, r_in, r_out, n, giro):
    meio = (r_in + r_out) / 2
    raio = min((r_out - r_in) * 0.33, math.pi * meio / n * 0.6)
    for i in range(n):
        x, y = _polar(meio, giro + i * 360 / n)
        p.circulo(x, y, raio)


def _arcos(p, r_in, r_out, n, giro):
    """Escamas: semicírculos apoiados na borda interna do anel."""
    raio = min((r_out - r_in) * 0.9, math.pi * r_in / n)
    for i in range(n):
        x, y = _polar(r_in, giro + i * 360 / n)
        p.circulo(x, y, raio)


def mandala(p: Caneta, semente: int = 1, nivel: int = 1) -> None:
    rnd = random.Random(semente)
    nivel = max(1, min(3, nivel))
    n = rnd.choice({1: [6, 8], 2: [8, 10, 12], 3: [12, 16]}[nivel])
    camadas = {1: 3, 2: 4, 3: 5}[nivel]
    r_max, r_min = 40.0, {1: 12.0, 2: 10.0, 3: 8.0}[nivel]
    passo = (r_max - r_min) / camadas

    # Coroa externa: pétalas ou pontas que saem do disco maior.
    giro0 = rnd.choice([0, 180 / n])
    if rnd.random() < 0.5:
        _petalas(p, r_max - 4, 49, n, giro0)
    else:
        _pontas(p, r_max - 4, 49, n, giro0)

    for i in range(camadas):
        r_out = r_max - i * passo
        r_in = r_out - passo
        giro = giro0 + (180 / n) * ((i + 1) % 2)
        p.circulo(C, C, r_out)
        estilo = rnd.choice(["petalas", "pontas", "bolinhas", "arcos"])
        if estilo == "arcos" and i == 0:
            estilo = "petalas"
        if estilo == "petalas":
            _petalas(p, r_in, r_out, n, giro)
        elif estilo == "pontas":
            _pontas(p, r_in, r_out, n, giro)
        elif estilo == "bolinhas":
            _bolinhas(p, r_in, r_out, n * (2 if nivel == 3 else 1), giro)
        else:
            _arcos(p, r_in, r_out, n, giro)

    p.circulo(C, C, r_min)
    if nivel == 1:
        p.circulo(C, C, r_min * 0.45)
    else:
        p.estrela(C, C, r_min * 0.85, pontas=max(5, n // 2))
