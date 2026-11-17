"""Gera a capa completa (contracapa + lombada + capa) num único PDF,
no tamanho exato que o KDP pede para o número de páginas do miolo.

A capa é o que vende: na busca da Amazon ela aparece do tamanho de um selo.
Por isso o título é enorme, colorido e com contorno grosso, e a ilustração
principal aparece "já pintada". Depois de gerar, confira a miniatura em
`capa_miniatura.png` (gerada pelo comando construir).
"""
from __future__ import annotations

import math
import random
import shutil
import subprocess
from pathlib import Path

from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.pdfgen.canvas import Canvas

from . import specs
from .atividades import descrever
from .caneta import Caneta
from .colecao import caixa_contracapa, selo_capa
from .colecao import dados as dados_colecao
from .desenhos import desenhar
from .fonts import FONTE, FONTE_NEGRITO

P = specs.POL
MARGEM_SEGURA = 0.375  # texto e desenhos importantes ficam longe do corte

CORES_TITULO = ["#FFEB3B", "#FF7043", "#66BB6A", "#42A5F5", "#AB47BC", "#EC407A", "#26C6DA"]
PALETA_DESENHO = ["#FFD54F", "#FF8A65", "#81C784", "#64B5F6", "#BA68C8", "#F06292",
                  "#4DD0E1", "#AED581", "#FFB74D"]


def _misturar(cor: Color, outra: Color, t: float) -> Color:
    return Color(cor.red + (outra.red - cor.red) * t, cor.green + (outra.green - cor.green) * t,
                 cor.blue + (outra.blue - cor.blue) * t)


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
    """Texto centralizado com contorno grosso (estilo "adesivo")."""
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
        # Isola o modo de texto (contorno/preenchido): no PDF ele vale até ser trocado.
        c.saveState()
        c.drawText(t)
        c.restoreState()


def _titulo_divertido(c: Canvas, cx: float, y: float, texto: str, tam: float,
                      cores: list[Color], inicio_cor: int = 0) -> int:
    """Uma linha de título com cada letra numa cor, levemente inclinada e saltitante,
    com sombra e contorno preto. Devolve o índice de cor para a próxima linha."""
    larguras = [c.stringWidth(ch, FONTE_NEGRITO, tam) for ch in texto]
    x = cx - sum(larguras) / 2
    k = inicio_cor
    for i, (ch, lw) in enumerate(zip(texto, larguras)):
        if ch == " ":
            x += lw
            continue
        salto = tam * 0.05 * (1 if i % 2 else -1)
        giro = 4 if i % 2 else -4
        c.saveState()
        c.translate(x + lw / 2, y + salto)
        c.rotate(giro)
        for dx, dy, modo, cor, esp in (
            (tam * 0.05, -tam * 0.05, 2, black, tam * 0.2),   # sombra
            (0, 0, 1, black, tam * 0.2),                      # contorno grosso
            (0, 0, 0, cores[k % len(cores)], 0),              # letra colorida
        ):
            t = c.beginText()
            t.setTextRenderMode(modo)
            t.setFont(FONTE_NEGRITO, tam)
            c.setStrokeColor(cor)
            c.setFillColor(cor)
            c.setLineWidth(esp)
            c.setLineJoin(1)
            t.setTextOrigin(-lw / 2 + dx, dy)
            t.textOut(ch)
            # Isola o modo de texto (contorno/preenchido): no PDF ele vale até ser trocado.
            c.saveState()
            c.drawText(t)
            c.restoreState()
        c.restoreState()
        x += lw
        k += 1
    return k


def _estampa(c: Canvas, largura: float, altura: float, fundo: Color, semente: str) -> None:
    """Fundo com estrelinhas e bolinhas num tom mais claro da cor de fundo."""
    rnd = random.Random(semente)
    claro = _misturar(fundo, white, 0.28)
    c.setFillColor(claro)
    c.setStrokeColor(claro)
    passo = 0.9 * P
    linhas = int(altura / passo) + 2
    colunas = int(largura / passo) + 2
    for j in range(linhas):
        for i in range(colunas):
            x = i * passo + (passo / 2 if j % 2 else 0) + rnd.uniform(-8, 8)
            y = j * passo + rnd.uniform(-8, 8)
            if rnd.random() < 0.5:
                c.circle(x, y, rnd.uniform(4, 7), stroke=0, fill=1)
            else:
                r = rnd.uniform(7, 11)
                giro = rnd.uniform(0, 72)
                caminho = c.beginPath()
                for k in range(10):
                    rr = r if k % 2 == 0 else r * 0.45
                    a = math.radians(giro + k * 36)
                    px, py = x + rr * math.cos(a), y + rr * math.sin(a)
                    (caminho.moveTo if k == 0 else caminho.lineTo)(px, py)
                caminho.close()
                c.drawPath(caminho, stroke=0, fill=1)


# Tema e pasta do livro sendo gerado (para achar ilustrações importadas na capa).
_CONTEXTO: dict = {}


def _ilustracao_colorida(caminho: Path, paleta: list[Color], semente: str):
    """Pinta automaticamente uma ilustração em traço: cada área fechada recebe uma cor
    da paleta (o fundo, que toca a borda, fica branco). Devolve um ImageReader."""
    import random

    import numpy as np
    from PIL import Image
    from reportlab.lib.utils import ImageReader
    from scipy import ndimage

    cinza = np.asarray(Image.open(caminho).convert("L"))
    tinta = cinza < 128
    rotulos, n = ndimage.label(~tinta)
    tamanhos = np.bincount(rotulos.ravel())
    borda = set(np.unique(np.concatenate([rotulos[0], rotulos[-1], rotulos[:, 0],
                                          rotulos[:, -1]])))
    rgb = np.full(cinza.shape + (3,), 255, dtype=np.uint8)
    cores = [(round(cor.red * 255), round(cor.green * 255), round(cor.blue * 255))
             for cor in paleta]
    rnd = random.Random(semente)
    rnd.shuffle(cores)
    mapa = np.zeros((n + 1, 3), dtype=np.uint8) + 255
    minimo = cinza.size * 0.0004  # áreas minúsculas ficam brancas (brilho dos olhos etc.)
    k = 0
    for i in np.argsort(-tamanhos):
        if i == 0 or i in borda or tamanhos[i] < minimo:
            continue
        mapa[i] = cores[k % len(cores)]
        k += 1
    rgb = mapa[rotulos]
    rgb[tinta] = (0, 0, 0)
    return ImageReader(Image.fromarray(rgb))


def _figura(c: Canvas, nome: str, x: float, y: float, lado: float, espessura: float,
            paleta: list[Color]) -> None:
    """Desenha a figura da capa: desenho em código colorido ou, com "imagem:NOME",
    a ilustração importada daquela página, pintada automaticamente."""
    if nome.startswith("imagem:"):
        alvo = nome.split(":", 1)[1]
        tema, base = _CONTEXTO.get("tema", {}), _CONTEXTO.get("base", Path("."))
        arquivo = next((p["arquivo"] for p in tema.get("paginas", [])
                        if p.get("tipo") == "imagem" and p.get("origem") == alvo), None)
        if not arquivo:
            raise ValueError(f"Capa: não há ilustração importada para '{alvo}'.")
        img = _ilustracao_colorida(Path(base) / arquivo, paleta, alvo)
        iw, ih = img.getSize()
        escala = min(lado / iw, lado / ih)
        w, h = iw * escala, ih * escala
        c.drawImage(img, x + (lado - w) / 2, y + (lado - h) / 2, w, h)
        return
    desenhar(nome, Caneta(c, x, y, lado, lado, espessura=espessura, paleta=paleta))


def _adesivo(c: Canvas, nome: str, cx: float, cy: float, tam: float, giro: float,
             paleta: list[Color]) -> None:
    """Desenho colorido num quadrado branco inclinado, como um adesivo."""
    c.saveState()
    c.translate(cx, cy)
    c.rotate(giro)
    c.setFillColor(Color(0, 0, 0, alpha=0.25))
    c.roundRect(-tam / 2 - 2, -tam / 2 - 9, tam + 8, tam + 8, 18, stroke=0, fill=1)
    c.setFillColor(white)
    c.setStrokeColor(black)
    c.setLineWidth(4)
    c.roundRect(-tam / 2 - 4, -tam / 2 - 4, tam + 8, tam + 8, 18, stroke=1, fill=1)
    _figura(c, nome, -tam / 2 + 6, -tam / 2 + 6, tam - 12, 3, paleta)
    c.restoreState()


def _selo_estourado(c: Canvas, cx: float, cy: float, r: float, linhas: list[tuple[str, float]],
                    cor: Color) -> None:
    c.saveState()
    c.translate(cx, cy)
    c.rotate(12)
    caminho = c.beginPath()
    pontas = 18
    for k in range(pontas * 2):
        rr = r if k % 2 == 0 else r * 0.84
        a = math.radians(k * 180 / pontas)
        (caminho.moveTo if k == 0 else caminho.lineTo)(rr * math.cos(a), rr * math.sin(a))
    caminho.close()
    c.setFillColor(cor)
    c.setStrokeColor(black)
    c.setLineWidth(4)
    c.setLineJoin(1)
    c.drawPath(caminho, stroke=1, fill=1)
    altura = sum(t * 1.15 for _, t in linhas)
    y = altura / 2 - linhas[0][1] * 0.8
    c.setFillColor(black)
    miolo = r * 0.8  # raio útil dentro das pontas
    for texto, tam in linhas:
        # A linha precisa caber na largura da estrela naquela altura.
        meio_y = y + tam * 0.35
        largura_util = 2 * math.sqrt(max(miolo ** 2 - meio_y ** 2, 0)) * 0.88
        while c.stringWidth(texto, FONTE_NEGRITO, tam) > largura_util and tam > 6:
            tam -= 0.5
        c.setFont(FONTE_NEGRITO, tam)
        c.drawCentredString(0, y, texto)
        y -= tam * 1.15
    c.restoreState()


def _o_que_tem(tema: dict) -> list[str]:
    """Lista "o que tem dentro" para a contracapa, a partir das páginas do tema."""
    cont = descrever(tema["paginas"])
    textos = {  # tipo: (singular, plural)
        "desenho": ("1 desenho grande para colorir", "{n} desenhos grandes para colorir"),
        "mandala": ("1 mandala", "{n} mandalas, do fácil ao desafiador"),
        "letra": ("1 letra para pintar", "{n} letras para pintar e treinar o traçado"),
        "labirinto": ("1 labirinto", "{n} labirintos"),
        "ligar_pontos": ("1 página de ligar os pontos", "{n} páginas de ligar os pontos"),
        "diferencas": ("1 jogo de encontrar as diferenças",
                       "{n} jogos de encontrar as diferenças"),
        "complete": ("1 desenho para completar", "{n} desenhos para completar"),
        "cubra": ("1 desenho para cobrir o pontilhado", "{n} desenhos para cobrir o pontilhado"),
        "imagem": ("1 ilustração para colorir", "{n} ilustrações para colorir"),
    }
    if "imagem" in cont:  # ilustrações importadas também são desenhos para colorir
        cont["desenho"] = cont.get("desenho", 0) + cont.pop("imagem")
    # Na ordem de textos: os desenhos (o principal argumento de venda) vêm primeiro.
    itens = [textos[t][0 if cont[t] == 1 else 1].format(n=cont[t]) for t in textos if t in cont]
    if cont.get("letra") == 26:
        itens = [i if not i.startswith("26 letras") else "Alfabeto completo de A a Z"
                 for i in itens]
    itens += ["Um desenho por folha, com o verso em branco", "Certificado de artista no final"]
    return itens


def _carregar_arte(conf: dict, base: Path | None):
    """Ilustração de capa (ex.: gerada no ChatGPT), ampliada para ~300 dpi."""
    from PIL import Image, ImageFilter

    img = Image.open(Path(base or ".") / conf["arte"]).convert("RGB")
    alvo_altura = round((specs.SANGRIA * 2 + 11) * 300)
    if img.height < alvo_altura:
        escala = alvo_altura / img.height
        img = img.resize((round(img.width * escala), alvo_altura), Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=3))
    return img


def _cor_do_ceu(img) -> Color:
    import numpy as np

    faixa = np.asarray(img)[: max(1, img.height // 8)].reshape(-1, 3)
    r, g, b = np.median(faixa, axis=0) / 255
    return Color(float(r), float(g), float(b))


def _desenhar_arte(c: Canvas, img, x: float, y: float, w: float, h: float) -> None:
    """Ilustração na frente: ocupa a largura toda e fica ancorada embaixo. O que sobra
    em cima é completado com a cor do céu (lisa nas ilustrações pedidas), o que abre
    mais espaço para o título sem cortar os personagens."""
    from reportlab.lib.utils import ImageReader

    escala = max(w / img.width, h * 0.92 / img.height)
    dw, dh = img.width * escala, img.height * escala
    c.saveState()
    caminho = c.beginPath()
    caminho.rect(x, y, w, h)
    c.clipPath(caminho, stroke=0, fill=0)
    c.setFillColor(_cor_do_ceu(img))
    c.rect(x, y, w, h, stroke=0, fill=1)
    c.drawImage(ImageReader(img), x + (w - dw) / 2, y, dw, dh)
    c.restoreState()


def gerar_capa(tema: dict, num_paginas: int, saida: Path,
               outros_volumes: list[str] | None = None,
               base: Path | None = None) -> specs.EspecCapa:
    _CONTEXTO.update(tema=tema, base=base or Path("."))
    larg, alt = specs.formato(tema.get("formato", "8.5x11"))
    espec = specs.EspecCapa(larg, alt, num_paginas, tema.get("papel", "branco"))
    conf = tema.get("capa", {})
    fundo = HexColor(conf.get("cor_fundo", "#4FC3F7"))
    arte = _carregar_arte(conf, base) if conf.get("arte") else None
    if arte is not None and not conf.get("cor_fundo_fixa"):
        fundo = _cor_do_ceu(arte)  # contracapa e lombada combinam com o céu da arte
    escuro = _misturar(fundo, black, 0.25)
    cores_titulo = [HexColor(x) for x in conf.get("cores_titulo", CORES_TITULO)]
    paleta = [HexColor(x) for x in conf.get("paleta", PALETA_DESENHO)]
    desenhos = conf.get("desenhos") or ["estrela"]

    W, H = espec.largura_total * P, espec.altura_total * P
    c = Canvas(str(saida), pagesize=(W, H), initialFontName=FONTE)
    c.setTitle(f"{tema['titulo']} — capa")
    c.setFillColor(fundo)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    _estampa(c, W, H, fundo, tema["titulo"])

    base_y = specs.SANGRIA * P
    seg = MARGEM_SEGURA * P
    fw, fh = larg * P, alt * P

    # ---- CAPA (frente) ---------------------------------------------------------------
    if arte is not None:
        _desenhar_arte(c, arte, espec.x_capa * P, 0, W - espec.x_capa * P, H)
    fx = espec.x_capa * P
    cx = fx + fw / 2
    titulo = tema["titulo"].upper()
    tam = conf.get("tamanho_titulo", 58 if arte is not None else 66)
    while True:
        linhas = _quebrar(c, titulo, FONTE_NEGRITO, tam, fw - 2 * seg - 20)
        if len(linhas) <= 3 or tam <= 34:
            break
        tam -= 2
    col = dados_colecao(tema)
    topo_titulo = base_y + fh - seg
    if col:
        topo_titulo -= selo_capa(c, cx, topo_titulo, col, fundo) + 16
    y = topo_titulo - tam * 0.95
    k = 0
    for linha in linhas:
        k = _titulo_divertido(c, cx, y, linha, tam, cores_titulo, k)
        y -= tam * 1.08

    if tema.get("subtitulo"):
        # Com arte, a faixa fica mais estreita e à esquerda: o lado direito é do selo.
        cx_sub = fx + fw * 0.42 if arte is not None else cx
        larg_max = fw * 0.62 if arte is not None else fw - 2 * seg - 60
        texto_sub = (conf.get("subtitulo_capa") if arte is not None else None) or tema["subtitulo"]
        sub = _quebrar(c, texto_sub, FONTE_NEGRITO, 17, larg_max)
        faixa_h = 18 + len(sub) * 21
        faixa_w = max(c.stringWidth(s, FONTE_NEGRITO, 17) for s in sub) + 44
        topo = y + tam * 0.45
        c.setFillColor(white)
        c.setStrokeColor(black)
        c.setLineWidth(3)
        c.roundRect(cx_sub - faixa_w / 2, topo - faixa_h, faixa_w, faixa_h, min(faixa_h / 2, 22),
                    stroke=1, fill=1)
        c.setFillColor(black)
        c.setFont(FONTE_NEGRITO, 17)
        ty = topo - 24
        for s in sub:
            c.drawCentredString(cx_sub, ty, s)
            ty -= 21
        y = topo - faixa_h - 10
    else:
        y += tam * 0.4

    rodape = base_y + seg + 44
    arte_topo, arte_base = y - 8, rodape + 6
    arte_h = arte_topo - arte_base
    if arte is None:  # sem arte: desenho principal num círculo e dois adesivos
        d = min(fw * 0.72, arte_h * 0.95)
        ccx, ccy = cx, arte_base + arte_h / 2
        c.setFillColor(escuro)
        c.circle(ccx + 7, ccy - 9, d / 2, stroke=0, fill=1)
        c.setFillColor(white)
        c.setStrokeColor(black)
        c.setLineWidth(6)
        c.circle(ccx, ccy, d / 2, stroke=1, fill=1)
        lado = d * (0.8 if desenhos[0].startswith("imagem:") else 0.74)
        _figura(c, desenhos[0], ccx - lado / 2, ccy - lado / 2, lado, 5, paleta)

        tam_ad = fw * 0.21
        adesivos = desenhos[1:3]
        lugares = [(fx + seg + tam_ad * 0.55, arte_base + tam_ad * 0.6, -9),
                   (fx + fw - seg - tam_ad * 0.55, arte_base + tam_ad * 0.6, 8)]
        for i, (nome, (ax, ay, giro)) in enumerate(zip(adesivos, lugares)):
            _adesivo(c, nome, ax, ay, tam_ad, giro, paleta[i * 3 + 1:] + paleta[: i * 3 + 1])

    n_paginas = len(tema["paginas"])
    tem_atividade = any(p.get("tipo") not in ("desenho", "mandala", "letra", "imagem")
                        for p in tema["paginas"])
    r_selo = fw * (0.1 if arte is not None else 0.12)
    if arte is not None:  # com arte: posição em fração da frente (padrão: sobre o sol)
        px, py = conf.get("posicao_selo", [0.85, 0.6])
        sx, sy = fx + fw * px, base_y + fh * py
    else:
        sx, sy = fx + fw - seg - r_selo * 0.9, arte_topo - r_selo * 0.75
    _selo_estourado(
        c, sx, sy, r_selo,
        [(str(n_paginas), r_selo * 0.5),
         ("DESENHOS E" if tem_atividade else "PÁGINAS", r_selo * 0.17),
         ("ATIVIDADES" if tem_atividade else "PARA PINTAR", r_selo * 0.17)],
        HexColor(conf.get("cor_selo", "#FFEB3B")),
    )

    if tema.get("faixa_etaria") and arte is None:  # com arte, a idade vai na faixa do subtítulo
        selo = f"Para {tema['faixa_etaria']}"
        c.setFillColor(white)
        c.setStrokeColor(black)
        c.setLineWidth(3)
        sw = c.stringWidth(selo, FONTE_NEGRITO, 18) + 36
        ey = (base_y + fh - seg - 40) if arte is not None else base_y + seg
        c.roundRect(fx + seg, ey, sw, 36, 18, stroke=1, fill=1)
        c.setFillColor(black)
        c.setFont(FONTE_NEGRITO, 18)
        c.drawString(fx + seg + 18, ey + 11, selo)
    if tema.get("autor"):
        aw = c.stringWidth(tema["autor"], FONTE_NEGRITO, 16)
        _texto_com_borda(c, fx + fw - seg - aw / 2, base_y + seg + 12, tema["autor"],
                         FONTE_NEGRITO, 16, white, borda=3)

    # ---- LOMBADA ---------------------------------------------------------------------
    lx0 = espec.x_lombada * P
    lw = espec.lombada * P
    c.setFillColor(escuro)
    c.rect(lx0, 0, lw, H, stroke=0, fill=1)
    if espec.aceita_texto_lombada:
        tam_l = min(lw - 2 * specs.MARGEM_LOMBADA * P, 18)
        texto = tema.get("titulo_lombada", tema["titulo"])
        c.saveState()
        c.translate(lx0 + lw / 2, base_y + fh / 2)
        c.rotate(-90)  # lê-se de cima para baixo, padrão de livros
        _texto_com_borda(c, 0, -tam_l * 0.35, texto, FONTE_NEGRITO, tam_l, white,
                         borda=tam_l * 0.12)
        c.restoreState()

    # ---- CONTRACAPA ------------------------------------------------------------------
    bx = espec.x_contracapa * P
    caixa_x, caixa_w = bx + seg, fw - 2 * seg
    itens = _o_que_tem(tema)
    texto = conf.get("texto_contracapa") or tema.get("anuncio", {}).get("descricao_curta", "")
    paragrafo = _quebrar(c, texto, FONTE, 14, caixa_w - 60) if texto else []
    caixa_h = 70 + len(itens) * 30 + (len(paragrafo) * 19 + 20 if paragrafo else 0)
    caixa_y = base_y + fh - seg - caixa_h
    c.setFillColor(escuro)
    c.roundRect(caixa_x + 7, caixa_y - 9, caixa_w, caixa_h, 24, stroke=0, fill=1)
    c.setFillColor(white)
    c.setStrokeColor(black)
    c.setLineWidth(4)
    c.roundRect(caixa_x, caixa_y, caixa_w, caixa_h, 24, stroke=1, fill=1)
    ty = caixa_y + caixa_h - 44
    _texto_com_borda(c, bx + fw / 2, ty, "O que tem dentro:", FONTE_NEGRITO, 26,
                     HexColor(CORES_TITULO[3]), borda=4)
    ty -= 40
    for i, item in enumerate(itens):
        c.setFillColor(HexColor(CORES_TITULO[(i + 1) % len(CORES_TITULO)]))
        c.setStrokeColor(black)
        c.setLineWidth(2)
        c.circle(caixa_x + 40, ty + 6, 10, stroke=1, fill=1)
        c.setFillColor(black)
        c.setFont(FONTE_NEGRITO, 13)
        c.drawCentredString(caixa_x + 40, ty + 1.5, "✔")
        c.setFont(FONTE_NEGRITO, 17)
        c.drawString(caixa_x + 60, ty, item)
        ty -= 30
    if paragrafo:
        ty -= 6
        c.setFont(FONTE, 14)
        for linha in paragrafo:
            c.drawCentredString(bx + fw / 2, ty, linha)
            ty -= 19

    base_livre = base_y + 0.25 * P + 1.2 * P
    if col:
        quadro_h = 1.25 * P
        quadro_y = base_y + seg + 46
        caixa_contracapa(c, bx + seg, quadro_y, fw - 2 * seg - 2.3 * P, quadro_h, col,
                         outros_volumes or [], paleta)
        base_livre = quadro_y + quadro_h
    mini = desenhos[:3]
    espaco_livre = caixa_y - base_livre - 40
    tam_m = min(fw * 0.26, espaco_livre)
    if tam_m > 60:
        esp = 26
        inicio = bx + (fw - len(mini) * tam_m - (len(mini) - 1) * esp) / 2
        for i, nome in enumerate(mini):
            _adesivo(c, nome, inicio + i * (tam_m + esp) + tam_m / 2,
                     caixa_y - 24 - tam_m / 2, tam_m * 0.9, (-6, 5, -4)[i % 3],
                     paleta[i * 2:] + paleta[: i * 2])
    if tema.get("faixa_etaria"):
        selo = f"Para {tema['faixa_etaria']}"
        c.setFillColor(white)
        c.setStrokeColor(black)
        c.setLineWidth(3)
        sw = c.stringWidth(selo, FONTE_NEGRITO, 16) + 32
        c.roundRect(bx + seg, base_y + seg, sw, 32, 16, stroke=1, fill=1)
        c.setFillColor(black)
        c.setFont(FONTE_NEGRITO, 16)
        c.drawString(bx + seg + 16, base_y + seg + 10, selo)
    # Área do código de barras (o KDP imprime aqui; deixe livre).
    c.setFillColor(white)
    c.rect(bx + fw - 0.25 * P - 2 * P, base_y + 0.25 * P, 2 * P, 1.2 * P, stroke=0, fill=1)
    c.save()
    return espec


def gerar_miniaturas(capa_pdf: Path, espec: specs.EspecCapa) -> list[Path]:
    """Recorta a frente da capa em PNG: uma grande (para conferir) e uma do tamanho
    que aparece na busca da Amazon. Precisa do pdftoppm (poppler)."""
    if not shutil.which("pdftoppm"):
        return []
    gerados = []
    for nome, largura_px in (("capa_frente", 600), ("capa_miniatura", 160)):
        r = largura_px / espec.largura_corte
        destino = capa_pdf.parent / nome
        subprocess.run([
            "pdftoppm", "-png", "-singlefile", "-r", f"{r:.3f}",
            "-x", str(round(espec.x_capa * r)), "-y", str(round(specs.SANGRIA * r)),
            "-W", str(round(espec.largura_corte * r)), "-H", str(round(espec.altura_corte * r)),
            str(capa_pdf), str(destino),
        ], check=True)
        gerados.append(destino.with_suffix(".png"))
    return gerados
