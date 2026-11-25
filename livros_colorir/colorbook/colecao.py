"""Coleção e mascote: dão identidade aos livros e fazem um vender o outro.

Ative no tema:

  "colecao": {"nome": "Coleção Gizinho", "volume": 1, "mascote": "gizinho"}

Com isso o mascote aparece na folha de rosto, nas instruções das atividades e
no certificado; a capa ganha o selo da coleção; e a contracapa lista os outros
livros com o mesmo nome de coleção que estiverem na pasta temas/.

Antes de registrar um nome de coleção ou mascote, confira no INPI se ele está livre.
"""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.colors import black, white
from reportlab.pdfgen.canvas import Canvas

from .caneta import Caneta
from .desenhos import desenhar
from .fonts import FONTE, FONTE_NEGRITO


def dados(tema: dict) -> dict | None:
    col = tema.get("colecao")
    if not col:
        return None
    return {"mascote": "gizinho", "volume": None, **col}


def outros_volumes(tema: dict, pasta_temas: Path) -> list[str]:
    """Títulos dos outros livros da mesma coleção, em ordem de volume."""
    col = dados(tema)
    if not col or not pasta_temas.is_dir():
        return []
    achados = []
    for arq in pasta_temas.glob("*.json"):
        try:
            outro = json.loads(arq.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        oc = outro.get("colecao") or {}
        if oc.get("nome") == col["nome"] and outro.get("titulo") != tema["titulo"]:
            achados.append((oc.get("volume") or 99, outro["titulo"]))
    return [t for _, t in sorted(achados)]


def balao(c: Canvas, x: float, y: float, w: float, texto: str, tam: float = 14,
          ponta: str = "esquerda") -> float:
    """Balão de fala com o texto quebrado em linhas. (x, y) é o canto superior
    esquerdo. Devolve a altura do balão."""
    linhas, linha = [], ""
    for palavra in texto.split():
        teste = f"{linha} {palavra}".strip()
        if c.stringWidth(teste, FONTE_NEGRITO, tam) > w - 28 and linha:
            linhas.append(linha)
            linha = palavra
        else:
            linha = teste
    linhas.append(linha)
    h = 22 + len(linhas) * tam * 1.25
    c.setStrokeColor(black)
    c.setFillColor(white)
    c.setLineWidth(2.5)
    c.setLineJoin(1)
    caminho = c.beginPath()
    if ponta == "esquerda":
        caminho.moveTo(x + 2, y - h * 0.65)
        caminho.lineTo(x - 18, y - h * 0.85)
        caminho.lineTo(x + 2, y - h * 0.4)
    else:  # embaixo
        caminho.moveTo(x + w * 0.2, y - h + 2)
        caminho.lineTo(x + w * 0.12, y - h - 18)
        caminho.lineTo(x + w * 0.35, y - h + 2)
    c.roundRect(x, y - h, w, h, 14, stroke=1, fill=1)
    c.drawPath(caminho, stroke=1, fill=1)
    c.setStrokeColor(white)  # apaga a emenda entre o balão e a ponta
    c.setLineWidth(3)
    if ponta == "esquerda":
        c.line(x + 1.5, y - h * 0.63, x + 1.5, y - h * 0.42)
    else:
        c.line(x + w * 0.21, y - h + 1.5, x + w * 0.34, y - h + 1.5)
    c.setFillColor(black)
    c.setFont(FONTE_NEGRITO, tam)
    ty = y - 14 - tam
    for ln in linhas:
        c.drawString(x + 14, ty, ln)
        ty -= tam * 1.25
    return h


def mascote(c: Canvas, nome: str, x: float, y: float, lado: float,
            espessura: float = 3.0) -> None:
    desenhar(nome, Caneta(c, x, y, lado, lado, espessura=espessura))


def selo_capa(c: Canvas, cx: float, y_topo: float, col: dict, cor_fundo) -> float:
    """Selo "COLEÇÃO X · VOL. N" com o mascote, centralizado. Devolve a altura usada."""
    texto = col["nome"].upper()
    if col.get("volume"):
        texto += f"  ·  VOL. {col['volume']}"
    tam = 15
    icone = 34
    w = c.stringWidth(texto, FONTE_NEGRITO, tam) + icone + 40
    h = 38
    x = cx - w / 2
    c.setFillColor(white)
    c.setStrokeColor(black)
    c.setLineWidth(3)
    c.roundRect(x, y_topo - h, w, h, h / 2, stroke=1, fill=1)
    desenhar(col["mascote"], Caneta(c, x + 10, y_topo - h + 2, icone, icone, espessura=1.8,
                                    paleta=[cor_fundo]))
    c.setFillColor(black)
    c.setFont(FONTE_NEGRITO, tam)
    c.drawString(x + icone + 22, y_topo - h + 13, texto)
    return h


def caixa_contracapa(c: Canvas, x: float, y: float, w: float, h: float, col: dict,
                     outros: list[str], paleta) -> None:
    """Quadro "Conheça a coleção" na contracapa, com o mascote e os outros títulos."""
    c.setFillColor(white)
    c.setStrokeColor(black)
    c.setLineWidth(3)
    c.roundRect(x, y, w, h, 18, stroke=1, fill=1)
    lado = h - 16
    desenhar(col["mascote"], Caneta(c, x + 6, y + 8, lado, lado, espessura=2.2, paleta=paleta))
    tx = x + lado + 16
    c.setFillColor(black)
    c.setFont(FONTE_NEGRITO, 16)
    c.drawString(tx, y + h - 26, f"Conheça a {col['nome']}!" if outros else col["nome"])
    c.setFont(FONTE, 12.5)
    ty = y + h - 46
    linhas = [f"• {t}" for t in outros[:3]] or [
        "Livros para pintar, brincar e aprender,",
        f"com o {col['mascote'].capitalize()} como companheiro."]
    for ln in linhas:
        while c.stringWidth(ln, FONTE, 12.5) > w - lado - 30 and len(ln) > 4:
            ln = ln[:-2] + "…"
        c.drawString(tx, ty, ln)
        ty -= 17
