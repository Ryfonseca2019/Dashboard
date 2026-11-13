"""Tipos de página que um tema pode usar.

Cada página recebe o canvas e a "área útil" (já descontando margens) e se
desenha dentro dela. Tipos disponíveis no JSON do tema:

  {"tipo": "desenho", "desenho": "gato", "legenda": "Gato"}
  {"tipo": "mandala", "semente": 3, "nivel": 1}
  {"tipo": "letra", "letra": "A", "palavra": "Abelha", "desenho": "flor"}
  {"tipo": "imagem", "arquivo": "imagens/dino.png", "legenda": "Dinossauro"}

O tipo "imagem" é a porta de entrada para ilustrações vindas de uma API de
geração de imagens: basta salvar o PNG em traço preto e apontar no tema.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import Color, black
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from .atividades import TIPOS as ATIVIDADES
from .caneta import Caneta
from .desenhos import desenhar
from .fonts import FONTE, FONTE_NEGRITO
from .mandalas import mandala

CINZA = Color(0.55, 0.55, 0.55)
CINZA_CLARO = Color(0.75, 0.75, 0.75)

Area = tuple[float, float, float, float]  # x, y, largura, altura (pontos)


def _legenda(c: Canvas, area: Area, texto: str | None) -> Area:
    """Escreve a legenda embaixo e devolve a área que sobra para o desenho."""
    x, y, w, h = area
    if not texto:
        return area
    tam = 26
    c.setFillColor(black)
    c.setFont(FONTE_NEGRITO, tam)
    c.drawCentredString(x + w / 2, y + 6, texto)
    return x, y + tam + 18, w, h - tam - 18


def _moldura(c: Canvas, area: Area) -> Area:
    x, y, w, h = area
    c.setStrokeColor(black)
    c.setLineWidth(2.5)
    c.roundRect(x, y, w, h, 18, stroke=1, fill=0)
    folga = 22
    return x + folga, y + folga, w - 2 * folga, h - 2 * folga


def pagina_desenho(c: Canvas, area: Area, pag: dict, moldura: bool) -> None:
    area = _legenda(c, area, pag.get("legenda"))
    if moldura:
        area = _moldura(c, area)
    desenhar(pag["desenho"], Caneta(c, *area))


def pagina_mandala(c: Canvas, area: Area, pag: dict, moldura: bool) -> None:
    area = _legenda(c, area, pag.get("legenda"))
    mandala(Caneta(c, *area, espessura=2.6 if pag.get("nivel", 1) > 1 else 3.2),
            semente=int(pag.get("semente", 1)), nivel=int(pag.get("nivel", 1)))


def _texto_vazado(c: Canvas, cx: float, y: float, texto: str, tam_max: float,
                  largura_max: float) -> None:
    """Palavra só com contorno, no maior tamanho que couber na largura."""
    tam = min(tam_max, tam_max * largura_max / max(c.stringWidth(texto, FONTE_NEGRITO, tam_max), 1))
    t = c.beginText()
    t.setTextRenderMode(1)
    t.setFont(FONTE_NEGRITO, tam)
    c.setStrokeColor(black)
    c.setLineWidth(max(1.5, tam / 30))
    c.setLineJoin(1)
    t.setTextOrigin(cx - c.stringWidth(texto, FONTE_NEGRITO, tam) / 2, y)
    t.textOut(texto)
    # Isola o modo de texto (contorno/preenchido): no PDF ele vale até ser trocado.
    c.saveState()
    c.drawText(t)
    c.restoreState()


def pagina_letra(c: Canvas, area: Area, pag: dict, moldura: bool) -> None:
    x, y, w, h = area
    letra = pag["letra"]
    palavra = pag.get("palavra", "")

    # Metade de cima: a letra maiúscula e minúscula vazadas.
    topo = Caneta(c, x, y + h * 0.5, w, h * 0.5)
    topo.texto_contorno(f"{letra.upper()}{letra.lower()}", 50, 82, 78, espessura=3)

    # Faixa do meio: desenho opcional ou a palavra.
    meio_h = h * 0.32
    meio_y = y + h * 0.16
    if pag.get("desenho"):
        desenhar(pag["desenho"], Caneta(c, x + w * 0.5, meio_y, w * 0.5, meio_h))
        _texto_vazado(c, x + w * 0.25, meio_y + meio_h / 2 - 15, palavra, 56, w * 0.46)
    else:
        _texto_vazado(c, x + w / 2, meio_y + meio_h / 2 - 25, palavra, 84, w * 0.95)

    # Linha de treino: letras em cinza tracejado para cobrir com o lápis.
    c.setStrokeColor(CINZA_CLARO)
    c.setLineWidth(1)
    base = y + 24
    c.line(x, base, x + w, base)
    c.setDash(4, 4)
    c.setStrokeColor(CINZA)
    tam = 54
    t = c.beginText()
    t.setTextRenderMode(1)
    t.setFont(FONTE, tam)
    passo = c.stringWidth(letra.upper() + "  ", FONTE, tam)
    qtd = max(1, int(w // passo))
    t.setTextOrigin(x + (w - qtd * passo) / 2 + passo * 0.15, base)
    t.textOut("  ".join([letra.upper()] * qtd))
    c.setLineWidth(1.2)
    # Isola o modo de texto (contorno/preenchido): no PDF ele vale até ser trocado.
    c.saveState()
    c.drawText(t)
    c.restoreState()
    c.setDash()


def pagina_imagem(c: Canvas, area: Area, pag: dict, moldura: bool, base: Path) -> None:
    area = _legenda(c, area, pag.get("legenda"))
    if moldura:
        area = _moldura(c, area)
    caminho = Path(pag["arquivo"])
    if not caminho.is_absolute():
        caminho = base / caminho
    if not caminho.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {caminho}")
    img = ImageReader(str(caminho))
    iw, ih = img.getSize()
    x, y, w, h = area
    escala = min(w / iw, h / ih)
    dw, dh = iw * escala, ih * escala
    c.drawImage(img, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, mask="auto")


def desenhar_pagina(c: Canvas, area: Area, pag: dict, moldura: bool, base: Path) -> None:
    tipo = pag.get("tipo", "desenho")
    if tipo == "desenho":
        pagina_desenho(c, area, pag, moldura)
    elif tipo == "mandala":
        pagina_mandala(c, area, pag, moldura)
    elif tipo == "letra":
        pagina_letra(c, area, pag, moldura)
    elif tipo == "imagem":
        pagina_imagem(c, area, pag, moldura, base)
    elif tipo in ATIVIDADES:
        ATIVIDADES[tipo](c, area, pag)
    else:
        raise ValueError(f"Tipo de página desconhecido: {tipo}")
