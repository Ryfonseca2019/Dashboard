"""Gera a capa completa (contracapa + lombada + capa) num único PDF,
no tamanho exato que o KDP pede para o número de páginas do miolo.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen.canvas import Canvas

from . import specs
from .caneta import Caneta
from .desenhos import desenhar
from .fonts import FONTE, FONTE_NEGRITO

P = specs.POL
MARGEM_SEGURA = 0.375  # texto e desenhos importantes ficam longe do corte


def _quebrar(c: Canvas, texto: str, fonte: str, tam: float, largura: float) -> list[str]:
    linhas: list[str] = []
    for paragrafo in texto.split("\n"):
        linha = ""
        for palavra in paragrafo.split():
            teste = f"{linha} {palavra}".strip()
            if c.stringWidth(teste, fonte, tam) > largura and linha:
                linhas.append(linha)
                linha = palavra
            else:
                linha = teste
        linhas.append(linha)
    return linhas


def _texto_com_borda(c: Canvas, x: float, y: float, texto: str, fonte: str, tam: float,
                     cor_texto, cor_borda=black, borda=None):
    """Texto centralizado com contorno grosso (estilo "adesivo"), bem legível na miniatura."""
    borda = tam * 0.16 if borda is None else borda
    largura = c.stringWidth(texto, fonte, tam)
    for modo, cor, esp in ((1, cor_borda, borda), (0, cor_texto, 0)):
        t = c.beginText()
        t.setTextRenderMode(modo)
        t.setFont(fonte, tam)
        c.setStrokeColor(cor)
        c.setFillColor(cor)
        c.setLineWidth(esp)
        c.setLineJoin(1)
        t.setTextOrigin(x - largura / 2, y)
        t.textOut(texto)
        c.drawText(t)


def gerar_capa(tema: dict, num_paginas: int, saida: Path) -> specs.EspecCapa:
    larg, alt = specs.formato(tema.get("formato", "8.5x11"))
    espec = specs.EspecCapa(larg, alt, num_paginas, tema.get("papel", "branco"))
    conf = tema.get("capa", {})
    fundo = HexColor(conf.get("cor_fundo", "#FFD54F"))
    destaque = HexColor(conf.get("cor_titulo", "#FFFFFF"))
    cores = [HexColor(cor) for cor in conf.get("cores_desenhos",
                                                 ["#FFFFFF", "#FFF3E0", "#E1F5FE", "#FCE4EC"])]

    c = Canvas(str(saida), pagesize=(espec.largura_total * P, espec.altura_total * P),
               initialFontName=FONTE)
    c.setTitle(f"{tema['titulo']} — capa")
    c.setFillColor(fundo)
    c.rect(0, 0, espec.largura_total * P, espec.altura_total * P, stroke=0, fill=1)

    base_y = specs.SANGRIA * P
    seg = MARGEM_SEGURA * P

    # ---- CAPA (frente) ---------------------------------------------------------------
    fx = espec.x_capa * P
    fw = larg * P
    fh = alt * P
    titulo_tam = conf.get("tamanho_titulo", 52)
    linhas = _quebrar(c, tema["titulo"].upper(), FONTE_NEGRITO, titulo_tam, fw - 2 * seg)
    y = base_y + fh - seg - titulo_tam
    for linha in linhas:
        _texto_com_borda(c, fx + fw / 2, y, linha, FONTE_NEGRITO, titulo_tam, destaque)
        y -= titulo_tam * 1.12
    if tema.get("subtitulo"):
        for linha in _quebrar(c, tema["subtitulo"], FONTE_NEGRITO, 20, fw - 2 * seg - 20):
            _texto_com_borda(c, fx + fw / 2, y - 6, linha, FONTE_NEGRITO, 20, white, borda=3.2)
            y -= 26

    desenhos = conf.get("desenhos") or ["estrela"]
    area_topo = y - 30
    area_base = base_y + seg + 60
    area_h = area_topo - area_base
    # Desenho principal grande + até 3 menores ao redor, como "adesivos".
    principal = desenhos[0]
    w_pri = min(fw * 0.62, area_h * 0.78)
    c.setFillColor(white)
    c.setStrokeColor(black)
    c.setLineWidth(5)
    cx = fx + fw / 2
    cy = area_base + area_h * 0.55
    c.circle(cx, cy, w_pri * 0.56, stroke=1, fill=1)
    desenhar(principal, Caneta(c, cx - w_pri / 2, cy - w_pri / 2, w_pri, w_pri,
                               espessura=4.5, preenchimento=cores[0]))
    pequenos = desenhos[1:4]
    posicoes = [(0.2, 0.12), (0.8, 0.12), (0.82, 0.9)]
    for i, (nome, (px, py)) in enumerate(zip(pequenos, posicoes)):
        tam = fw * 0.24
        x0 = fx + fw * px - tam / 2
        y0 = area_base + area_h * py - tam / 2
        c.setFillColor(white)
        c.setLineWidth(4)
        c.roundRect(x0 - 6, y0 - 6, tam + 12, tam + 12, 22, stroke=1, fill=1)
        desenhar(nome, Caneta(c, x0, y0, tam, tam, espessura=3,
                              preenchimento=cores[(i + 1) % len(cores)]))
    if tema.get("faixa_etaria"):
        selo = f"Para {tema['faixa_etaria']}"
        c.setFillColor(white)
        c.setLineWidth(3)
        sw = c.stringWidth(selo, FONTE_NEGRITO, 16) + 36
        c.roundRect(fx + seg, base_y + seg, sw, 34, 17, stroke=1, fill=1)
        c.setFillColor(black)
        c.setFont(FONTE_NEGRITO, 16)
        c.drawString(fx + seg + 18, base_y + seg + 11, selo)
    if tema.get("autor"):
        _texto_com_borda(c, fx + fw - seg - c.stringWidth(tema["autor"], FONTE_NEGRITO, 16) / 2,
                         base_y + seg + 11, tema["autor"], FONTE_NEGRITO, 16, white, borda=3)

    # ---- LOMBADA ---------------------------------------------------------------------
    if espec.aceita_texto_lombada:
        lx = (espec.x_lombada + espec.lombada / 2) * P
        tam = min(espec.lombada * P - 2 * specs.MARGEM_LOMBADA * P, 18)
        texto = tema.get("titulo_lombada", tema["titulo"])
        c.saveState()
        c.translate(lx, base_y + fh / 2)
        c.rotate(-90)  # lê-se de cima para baixo, padrão de livros
        c.setFillColor(black)
        c.setFont(FONTE_NEGRITO, tam)
        c.drawCentredString(0, -tam * 0.35, texto)
        c.restoreState()

    # ---- CONTRACAPA ------------------------------------------------------------------
    bx = espec.x_contracapa * P
    texto = conf.get("texto_contracapa") or tema.get("anuncio", {}).get("descricao_curta", "")
    caixa_w = fw - 2 * seg
    linhas = _quebrar(c, texto, FONTE, 15, caixa_w - 50)
    caixa_h = 40 + len(linhas) * 22
    caixa_y = base_y + fh - seg - caixa_h
    c.setFillColor(white)
    c.setStrokeColor(black)
    c.setLineWidth(3)
    c.roundRect(bx + seg, caixa_y, caixa_w, caixa_h, 18, stroke=1, fill=1)
    c.setFillColor(black)
    c.setFont(FONTE, 15)
    ty = caixa_y + caixa_h - 32
    for linha in linhas:
        c.drawCentredString(bx + fw / 2, ty, linha)
        ty -= 22
    mini = desenhos[:3]
    tam = fw * 0.24
    espaco = 24
    inicio = bx + (fw - len(mini) * tam - (len(mini) - 1) * espaco) / 2
    for i, nome in enumerate(mini):
        x0 = inicio + i * (tam + espaco)
        desenhar(nome, Caneta(c, x0, caixa_y - tam - 40, tam, tam, espessura=2.6,
                              preenchimento=cores[i % len(cores)]))
    # Área do código de barras (o KDP imprime aqui; deixe livre).
    c.setFillColor(white)
    c.rect(bx + fw - 0.25 * P - 2 * P, base_y + 0.25 * P, 2 * P, 1.2 * P, stroke=0, fill=1)
    c.save()
    return espec
