"""Especificações de impressão sob demanda (padrão Amazon KDP, brochura).

Todas as medidas estão em polegadas, que é a unidade usada pelo KDP.
Confira os valores na documentação oficial antes de publicar, pois as
regras das gráficas mudam de tempos em tempos.
"""
from __future__ import annotations

from dataclasses import dataclass

POL = 72.0  # pontos PDF por polegada

# Tamanhos de corte (largura, altura) mais usados para livros de colorir.
FORMATOS = {
    "8.5x11": (8.5, 11.0),     # padrão de mercado para livros de colorir
    "8x10": (8.0, 10.0),
    "8.25x8.25": (8.25, 8.25),  # quadrado, bom para os pequenos
    "a4": (8.27, 11.69),
}

# Espessura por página (pol/página) para calcular a lombada.
PAPEL = {
    "branco": 0.002252,        # preto e branco, papel branco
    "creme": 0.0025,           # preto e branco, papel creme
    "colorido": 0.002252,      # colorido padrão
    "colorido_premium": 0.002347,
}

SANGRIA = 0.125          # sangria (bleed) em cada borda externa
MIN_PAGINAS = 24          # mínimo do KDP para brochura
MAX_PAGINAS = 828         # máximo do KDP para P&B em 8.5x11 (varia por formato)
MIN_PAGINAS_TEXTO_LOMBADA = 79  # abaixo disso o KDP não aceita texto na lombada
MARGEM_LOMBADA = 0.0625   # folga de cada lado do texto da lombada


def margem_interna(num_paginas: int) -> float:
    """Margem mínima do lado da costura (gutter) exigida pelo KDP."""
    if num_paginas <= 150:
        return 0.375
    if num_paginas <= 300:
        return 0.5
    if num_paginas <= 500:
        return 0.625
    if num_paginas <= 700:
        return 0.75
    return 0.875


@dataclass(frozen=True)
class EspecMiolo:
    largura: float
    altura: float
    num_paginas: int
    margem_externa: float = 0.5  # o mínimo é 0.25; usamos folga para crianças pintarem

    @property
    def margem_interna(self) -> float:
        # Acrescenta folga à margem mínima para o desenho não "sumir" na costura.
        return margem_interna(self.num_paginas) + 0.25

    @property
    def tamanho_pt(self) -> tuple[float, float]:
        return self.largura * POL, self.altura * POL


@dataclass(frozen=True)
class EspecCapa:
    largura_corte: float
    altura_corte: float
    num_paginas: int
    papel: str = "branco"

    @property
    def lombada(self) -> float:
        return self.num_paginas * PAPEL[self.papel]

    @property
    def largura_total(self) -> float:
        return SANGRIA + self.largura_corte + self.lombada + self.largura_corte + SANGRIA

    @property
    def altura_total(self) -> float:
        return SANGRIA + self.altura_corte + SANGRIA

    @property
    def aceita_texto_lombada(self) -> bool:
        return self.num_paginas >= MIN_PAGINAS_TEXTO_LOMBADA

    # Posições (em polegadas, a partir da borda esquerda do arquivo).
    @property
    def x_contracapa(self) -> float:
        return SANGRIA

    @property
    def x_lombada(self) -> float:
        return SANGRIA + self.largura_corte

    @property
    def x_capa(self) -> float:
        return SANGRIA + self.largura_corte + self.lombada


def formato(nome: str) -> tuple[float, float]:
    try:
        return FORMATOS[nome.lower()]
    except KeyError as exc:
        raise ValueError(
            f"Formato '{nome}' desconhecido. Use um destes: {', '.join(FORMATOS)}"
        ) from exc
