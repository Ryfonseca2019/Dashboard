"""Guia de estilo em números: as regras que o auditor confere em cada página.

Os valores são o ponto de partida e devem ser ajustados com o que você
observar na cópia de prova impressa (veja PROVA.md). Mudou aqui, muda a régua
do auditor para todos os livros.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Perfil:
    nome: str
    traco_min_pt: float      # linhas mais finas que isso somem no papel ou frustram a criança
    area_min_cm2: float      # áreas menores que isso são difíceis de pintar dentro
    areas_max: int           # mais áreas que isso deixa a página cansativa
    areas_min: int           # menos que isso deixa a página "vazia"
    ocupacao_min: float      # fração da área útil que o desenho deve ocupar


PERFIS = {
    # 2 a 5 anos: giz de cera grosso, coordenação motora começando.
    "pequenos": Perfil("2 a 5 anos", traco_min_pt=1.5, area_min_cm2=0.8, areas_max=45,
                       areas_min=4, ocupacao_min=0.60),
    # 5 a 10 anos: lápis de cor e canetinha, gostam de detalhe.
    "maiores": Perfil("5 a 10 anos", traco_min_pt=1.0, area_min_cm2=0.2, areas_max=220,
                      areas_min=8, ocupacao_min=0.65),
}


def perfil_do_tema(tema: dict) -> Perfil:
    """Escolhe o perfil pela idade mínima da faixa etária do tema ("2 a 5 anos" → pequenos)."""
    if tema.get("perfil") in PERFIS:
        return PERFIS[tema["perfil"]]
    numeros = [int(n) for n in re.findall(r"\d+", tema.get("faixa_etaria", ""))]
    return PERFIS["pequenos" if not numeros or numeros[0] < 5 else "maiores"]
