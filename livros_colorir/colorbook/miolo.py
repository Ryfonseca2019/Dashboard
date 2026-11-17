"""Monta o miolo (interior) do livro em PDF pronto para impressão.

Estrutura gerada:
  1  Folha de rosto (título)          — página direita
  2  Direitos autorais                — página esquerda
  3  "Este livro pertence a"          — direita
  4  Teste suas cores                 — esquerda
  5+ Cada desenho numa página DIREITA, com o verso em branco
     (a tinta de canetinha não atravessa e estraga o próximo desenho)
  .. Certificado "Parabéns!" e páginas finais até atingir o mínimo do KDP.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from reportlab.lib.colors import black
from reportlab.pdfgen.canvas import Canvas

from . import specs
from .caneta import Caneta
from .desenhos import desenhar
from .fonts import FONTE, FONTE_NEGRITO
from .atividades import TIPOS as ATIVIDADES
from .colecao import balao
from .colecao import dados as dados_colecao
from .paginas import CINZA, desenhar_pagina


def planejar(tema: dict) -> list[dict]:
    """Devolve a lista de páginas na ordem final (sem desenhar nada)."""
    plano: list[dict] = [
        {"tipo": "_rosto"},
        {"tipo": "_direitos"},
        {"tipo": "_pertence"},
        {"tipo": "_teste_cores"},
    ]
    verso = tema.get("verso_em_branco", True)
    from .estilo import perfil_do_tema

    area_min = perfil_do_tema(tema).area_min_cm2 if tema.get("simplificar_detalhes", True) else 0
    for pag in tema["paginas"]:
        if area_min and pag.get("tipo", "desenho") == "desenho":
            pag = {**pag, "_area_min_cm2": area_min}
        if pag.get("tipo", "desenho") == "desenho":
            # Contorno externo grosso (0 desliga). Veja desenhos.desenhar().
            pag = {**pag, "_contorno": tema.get("contorno_grosso", 2.4)}
        if tema.get("colecao") and pag.get("tipo") in ATIVIDADES:
            pag = {**pag, "_mascote": tema["colecao"].get("mascote", "gizinho")}
        if tema.get("cenarios") and pag.get("tipo", "desenho") == "desenho" and "cena" not in pag:
            from .cenas import CENA_PADRAO

            pag = {**pag, "cena": CENA_PADRAO.get(pag["desenho"], "campo")}
        plano.append(pag)
        if verso:
            plano.append({"tipo": "_verso"})
    if len(plano) % 2 == 1:
        plano.append({"tipo": "_verso"})
    plano.append({"tipo": "_certificado"})
    plano.append({"tipo": "_verso"})
    while len(plano) < specs.MIN_PAGINAS:
        plano.append({"tipo": "_anotacoes"})
    if len(plano) % 2 == 1:
        plano.append({"tipo": "_verso"})
    return plano


def _area_util(espec: specs.EspecMiolo, numero: int) -> tuple[float, float, float, float]:
    """Área dentro das margens. Página ímpar = direita (costura à esquerda)."""
    P = specs.POL
    m_int, m_ext = espec.margem_interna * P, espec.margem_externa * P
    m_sup, m_inf = espec.margem_externa * P, espec.margem_externa * P
    esquerda = m_int if numero % 2 == 1 else m_ext
    direita = m_ext if numero % 2 == 1 else m_int
    larg, alt = espec.tamanho_pt
    return esquerda, m_inf, larg - esquerda - direita, alt - m_sup - m_inf


def _centro(c: Canvas, x, y, w, texto, fonte, tam):
    c.setFont(fonte, tam)
    c.setFillColor(black)
    c.drawCentredString(x + w / 2, y, texto)


def _paragrafo(c: Canvas, x, y, w, texto, fonte=FONTE, tam=11, entrelinha=1.45):
    """Quebra simples de linha centralizada; devolve o y final."""
    c.setFont(fonte, tam)
    for paragrafo in texto.split("\n"):
        linha = ""
        for palavra in paragrafo.split():
            teste = f"{linha} {palavra}".strip()
            if c.stringWidth(teste, fonte, tam) > w and linha:
                c.drawCentredString(x + w / 2, y, linha)
                y -= tam * entrelinha
                linha = palavra
            else:
                linha = teste
        c.drawCentredString(x + w / 2, y, linha)
        y -= tam * entrelinha
    return y


def _pagina_especial(c: Canvas, area, pag, tema: dict) -> None:
    x, y, w, h = area
    tipo = pag["tipo"]
    if tipo == "_verso":
        if tema.get("aviso_verso", True):
            c.setFillColor(CINZA)
            c.setFont(FONTE, 8)
            c.drawCentredString(x + w / 2, y + 4,
                                "Página em branco de propósito, para a tinta não passar para o desenho.")
    elif tipo == "_rosto":
        topo = y + h
        _paragrafo(c, x, topo - 90, w, tema["titulo"], FONTE_NEGRITO, 40, 1.2)
        if tema.get("subtitulo"):
            _paragrafo(c, x, topo - 230, w, tema["subtitulo"], FONTE, 18)
        col = dados_colecao(tema)
        if col:
            lado = w * 0.42
            desenhar(col["mascote"], Caneta(c, x + w * 0.04, y + h * 0.14, lado, lado), 2.4)
            nome = col["mascote"].capitalize()
            balao(c, x + w * 0.5, y + h * 0.14 + lado * 0.95, w * 0.48,
                  f"Oi! Eu sou o {nome}. Vamos pintar juntos?", tam=17)
            rotulo = col["nome"] + (f" · Volume {col['volume']}" if col.get("volume") else "")
            _centro(c, x, y + 70, w, rotulo, FONTE_NEGRITO, 14)
        else:
            destaque = (tema.get("capa", {}).get("desenhos") or ["estrela"])[0]
            desenhar(destaque, Caneta(c, x + w * 0.2, y + h * 0.18, w * 0.6, h * 0.45))
        _centro(c, x, y + 40, w, tema.get("autor", ""), FONTE, 16)
    elif tipo == "_direitos":
        ano = dt.date.today().year
        texto = (
            f"{tema['titulo']}\n"
            f"© {ano} {tema.get('autor', '')}. Todos os direitos reservados.\n"
            "Nenhuma parte deste livro pode ser reproduzida para venda sem autorização.\n"
            "As páginas podem ser copiadas para uso pessoal da criança.\n"
            + (f"ISBN: {tema['isbn']}\n" if tema.get("isbn") else "")
            + tema.get("nota_direitos", "")
        )
        _paragrafo(c, x, y + 140, w, texto, FONTE, 10)
    elif tipo == "_pertence":
        _centro(c, x, y + h * 0.72, w, "Este livro pertence a:", FONTE_NEGRITO, 32)
        c.setLineWidth(2)
        c.setStrokeColor(black)
        c.line(x + w * 0.1, y + h * 0.58, x + w * 0.9, y + h * 0.58)
        desenhar("coracao", Caneta(c, x + w * 0.3, y + h * 0.12, w * 0.4, h * 0.35))
    elif tipo == "_teste_cores":
        _centro(c, x, y + h - 60, w, "Teste suas cores aqui!", FONTE_NEGRITO, 28)
        _paragrafo(c, x, y + h - 95, w,
                   "Pinte cada bolinha para ver como fica cada lápis ou canetinha.", FONTE, 12)
        p = Caneta(c, x, y + h * 0.08, w, h * 0.7)
        for linha in range(5):
            for col in range(5):
                p.circulo(14 + col * 18, 12 + linha * 19, 7.5)
    elif tipo == "_certificado":
        c.setLineWidth(4)
        c.roundRect(x, y + h * 0.2, w, h * 0.65, 24, stroke=1, fill=0)
        _centro(c, x, y + h * 0.74, w, "Parabéns!", FONTE_NEGRITO, 46)
        _paragrafo(c, x + 30, y + h * 0.66, w - 60,
                   "Você pintou o livro inteirinho! Você é um artista incrível.", FONTE, 18)
        c.setLineWidth(2)
        c.line(x + w * 0.15, y + h * 0.32, x + w * 0.85, y + h * 0.32)
        _centro(c, x, y + h * 0.28, w, "Nome do artista", FONTE, 12)
        col = dados_colecao(tema)
        if col:
            lado = h * 0.17
            desenhar(col["mascote"], Caneta(c, x + w * 0.22, y + h * 0.36, lado, lado), 2.4)
            p = Caneta(c, x + w * 0.55, y + h * 0.36, lado, lado)
            p.estrela(50, 50, 45)
            _centro(c, x, y + h * 0.215, w, f"Com carinho, {col['mascote'].capitalize()}",
                    FONTE_NEGRITO, 13)
        else:
            p = Caneta(c, x + w * 0.35, y + h * 0.36, w * 0.3, h * 0.2)
            p.estrela(50, 50, 45)
    elif tipo == "_anotacoes":
        _centro(c, x, y + h - 60, w, "Desenhe o que quiser!", FONTE_NEGRITO, 28)
        c.setLineWidth(2.5)
        c.roundRect(x, y, w, h - 100, 18, stroke=1, fill=0)


def gerar_miolo(tema: dict, saida: Path, base: Path) -> int:
    """Gera o PDF do miolo e devolve o número de páginas."""
    plano = planejar(tema)
    largura, altura = specs.formato(tema.get("formato", "8.5x11"))
    espec = specs.EspecMiolo(largura, altura, len(plano))
    moldura = tema.get("moldura", True)

    c = Canvas(str(saida), pagesize=espec.tamanho_pt, initialFontName=FONTE)
    c.setTitle(tema["titulo"])
    c.setAuthor(tema.get("autor", ""))
    c.setSubject("Livro de colorir — miolo")
    for numero, pag in enumerate(plano, start=1):
        area = _area_util(espec, numero)
        if pag["tipo"].startswith("_"):
            _pagina_especial(c, area, pag, tema)
        else:
            desenhar_pagina(c, area, pag, moldura, base)
        c.showPage()
    c.save()
    return len(plano)
