"""Auditor de qualidade: mede cada página de conteúdo e dá uma nota de 0 a 100.

    python -m colorbook auditar temas/primeiros_desenhos.json

O que é medido (com as regras de estilo.py para a faixa etária do livro):
  - ocupação: quanto da área útil o desenho realmente usa;
  - traço fino: parte do traço mais fina que o mínimo da idade;
  - áreas pequenas: regiões fechadas pequenas demais para pintar dentro;
  - complexidade: quantas áreas para pintar a página tem;
  - repetição: páginas parecidas demais entre si.

Gera saida/<id>/qualidade.md (relatório) e qualidade.png (prévia com as notas).
Precisa do pdftoppm (poppler), numpy, scipy e pillow.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen.canvas import Canvas
from scipy import ndimage

from . import specs
from .estilo import Perfil, perfil_do_tema
from .fonts import FONTE
from .miolo import _area_util, planejar
from .paginas import desenhar_pagina

DPI = 150
PX_POR_PT = DPI / 72.0
CM2_POR_PX = (2.54 / DPI) ** 2
# Páginas com traço fino de propósito (pontilhado para cobrir, números) não são
# cobradas por traço fino.
SEM_REGRA_DE_TRACO = {"cubra", "ligar_pontos", "letra", "labirinto"}
# Atividades não são "desenhos para pintar": não contam áreas nem complexidade.
SEM_REGRA_DE_AREAS = {"cubra", "ligar_pontos", "labirinto", "letra", "complete", "diferencas"}


@dataclass
class Resultado:
    indice: int            # posição entre as páginas de conteúdo (1, 2, ...)
    pagina_livro: int      # número da página no PDF do miolo
    rotulo: str
    tipo: str
    ocupacao: float = 0.0
    traco_fino: float = 0.0
    areas: int = 0
    areas_pequenas: int = 0
    nota: int = 100
    problemas: list[str] = field(default_factory=list)
    miniatura: np.ndarray | None = None
    mascara_pequenas: np.ndarray | None = None


def _rotulo(pag: dict) -> str:
    tipo = pag.get("tipo", "desenho")
    detalhe = pag.get("desenho") or pag.get("figura") or pag.get("letra") or pag.get("arquivo")
    if tipo == "mandala":
        detalhe = f"semente {pag.get('semente', 1)}, nível {pag.get('nivel', 1)}"
    return f"{tipo}: {detalhe}" if detalhe else tipo


def _renderizar(tema: dict, base: Path, pasta_tmp: Path) -> tuple[list[tuple[int, dict]], Path]:
    """Desenha só as páginas de conteúdo, sem moldura e sem legenda, na mesma área
    que elas têm no livro. Assim a medição pega o desenho e não a moldura."""
    plano = planejar(tema)
    largura, altura = specs.formato(tema.get("formato", "8.5x11"))
    espec = specs.EspecMiolo(largura, altura, len(plano))
    conteudo = [(n, p) for n, p in enumerate(plano, 1) if not p["tipo"].startswith("_")]
    pdf = pasta_tmp / "auditoria.pdf"
    c = Canvas(str(pdf), pagesize=espec.tamanho_pt)
    for numero, pag in conteudo:
        limpa = {k: v for k, v in pag.items() if k != "legenda"}
        desenhar_pagina(c, _area_util(espec, numero), limpa, False, base)
        c.showPage()
    c.save()
    subprocess.run(["pdftoppm", "-gray", "-r", str(DPI), str(pdf), str(pasta_tmp / "p")],
                   check=True)
    return conteudo, espec


def _medir(img: np.ndarray, area_px: tuple[int, int, int, int], perfil: Perfil,
           r: Resultado) -> None:
    x0, y0, x1, y1 = area_px
    # < 200 conta também o pontilhado cinza das páginas de "cubra".
    tinta = img[y0:y1, x0:x1] < 200
    total_tinta = int(tinta.sum())
    if total_tinta == 0:
        r.problemas.append("Página vazia.")
        r.nota = 0
        return

    # Ocupação: caixa que envolve a tinta, em relação à área útil.
    linhas = np.where(tinta.any(axis=1))[0]
    colunas = np.where(tinta.any(axis=0))[0]
    caixa = (linhas[-1] - linhas[0] + 1) * (colunas[-1] - colunas[0] + 1)
    r.ocupacao = caixa / tinta.size

    # Traço fino: o que some numa "abertura" do tamanho do traço mínimo.
    k = max(2, round(perfil.traco_min_pt * PX_POR_PT))
    aberto = ndimage.binary_opening(tinta, structure=np.ones((k, k)))
    r.traco_fino = float((tinta & ~aberto).sum()) / total_tinta

    # Áreas para pintar: regiões brancas fechadas (sem contar o fundo, que toca a borda).
    rotulos, n = ndimage.label(~tinta)
    if n:
        tamanhos = np.bincount(rotulos.ravel())[1:]
        borda = set(np.unique(np.concatenate([rotulos[0], rotulos[-1], rotulos[:, 0],
                                              rotulos[:, -1]]))) - {0}
        ruido = 0.02 / CM2_POR_PX           # frestas de anti-serrilhado, não são áreas
        pequena = perfil.area_min_cm2 / CM2_POR_PX
        validas = [t for i, t in enumerate(tamanhos, 1) if i not in borda and t >= ruido]
        r.areas = len(validas)
        r.areas_pequenas = sum(1 for t in validas if t < pequena)
        if r.tipo not in SEM_REGRA_DE_AREAS:
            ids = [i for i, t in enumerate(tamanhos, 1)
                   if i not in borda and ruido <= t < pequena]
            r.mascara_pequenas = np.isin(rotulos, ids)

    # Miniatura para comparar páginas parecidas.
    h, w = tinta.shape
    bh, bw = h // 24, w // 24
    r.miniatura = tinta[: bh * 24, : bw * 24].reshape(24, bh, 24, bw).mean(axis=(1, 3))


def _pontuar(r: Resultado, perfil: Perfil) -> None:
    if r.ocupacao < perfil.ocupacao_min:
        r.nota -= 15
        r.problemas.append(f"Desenho ocupa só {r.ocupacao:.0%} da área útil "
                           f"(mínimo {perfil.ocupacao_min:.0%}): sobra espaço em branco.")
    if r.tipo not in SEM_REGRA_DE_TRACO and r.traco_fino > 0.08:
        r.nota -= 20 if r.traco_fino > 0.2 else 10
        r.problemas.append(f"{r.traco_fino:.0%} do traço é mais fino que "
                           f"{perfil.traco_min_pt} pt (detalhes difíceis para a idade).")
    if r.tipo not in SEM_REGRA_DE_AREAS:
        if r.areas_pequenas:
            r.nota -= min(30, r.areas_pequenas * 4)
            r.problemas.append(f"{r.areas_pequenas} área(s) menores que "
                               f"{perfil.area_min_cm2} cm² (difíceis de pintar dentro).")
        if r.areas > perfil.areas_max:
            r.nota -= 10
            r.problemas.append(f"{r.areas} áreas: cansativo para {perfil.nome} "
                               f"(máximo {perfil.areas_max}).")
        if r.areas < perfil.areas_min:
            r.nota -= 10
            r.problemas.append(f"Só {r.areas} áreas para pintar: página pobre "
                               f"(mínimo {perfil.areas_min}).")
    r.nota = max(0, r.nota)


def _repeticoes(resultados: list[Resultado]) -> list[tuple[Resultado, Resultado, float]]:
    pares = []
    for i, a in enumerate(resultados):
        for b in resultados[i + 1:]:
            if a.miniatura is None or b.miniatura is None:
                continue
            va, vb = a.miniatura.ravel() - a.miniatura.mean(), b.miniatura.ravel() - b.miniatura.mean()
            den = np.linalg.norm(va) * np.linalg.norm(vb)
            sim = float(va @ vb / den) if den else 0.0
            if sim > 0.85:
                pares.append((a, b, sim))
    return pares


def _prancha(resultados, imagens, destino: Path) -> None:
    """Prévia com todas as páginas de conteúdo e a nota de cada uma."""
    larg = 150
    miniaturas = []
    for r, img in zip(resultados, imagens):
        im = Image.fromarray(img).convert("RGB")
        if r.mascara_pequenas is not None and r.mascara_pequenas.any():
            # Pinta de vermelho as áreas pequenas demais, para mostrar onde estão.
            rgb = np.array(im)
            rgb[r.mascara_pequenas] = (229, 57, 53)
            im = Image.fromarray(rgb)
        im.thumbnail((larg, larg * 2))
        miniaturas.append(im)
    alt = max(m.height for m in miniaturas) + 34
    cols = 8
    linhas = (len(miniaturas) + cols - 1) // cols
    prancha = Image.new("RGB", (cols * (larg + 10) + 10, linhas * (alt + 10) + 10), "white")
    d = ImageDraw.Draw(prancha)
    try:
        fonte = ImageFont.truetype(str(Path(__file__).parent / "fonts" / f"{FONTE}.ttf"), 13)
    except OSError:
        fonte = ImageFont.load_default()
    for i, (r, m) in enumerate(zip(resultados, miniaturas)):
        x = 10 + (i % cols) * (larg + 10)
        y = 10 + (i // cols) * (alt + 10)
        prancha.paste(m, (x, y + 30))
        cor = (46, 125, 50) if r.nota >= 85 else (245, 124, 0) if r.nota >= 65 else (198, 40, 40)
        d.rectangle([x - 3, y - 3, x + larg + 3, y + alt + 3], outline=cor, width=4)
        d.rectangle([x - 3, y - 3, x + larg + 3, y + 24], fill=cor)
        d.text((x + 4, y + 3), f"p.{r.pagina_livro}  nota {r.nota}", fill="white", font=fonte)
    prancha.save(destino)


def auditar(arquivo_tema: Path, saida: Path) -> dict:
    if not shutil.which("pdftoppm"):
        raise RuntimeError("O auditor precisa do pdftoppm (instale o poppler).")
    tema = json.loads(arquivo_tema.read_text(encoding="utf-8"))
    perfil = perfil_do_tema(tema)
    pasta = saida / tema.get("id", arquivo_tema.stem)
    pasta.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        conteudo, espec = _renderizar(tema, arquivo_tema.parent, tmp_path)
        arquivos = sorted(tmp_path.glob("p-*.pgm"), key=lambda f: int(f.stem.split("-")[1]))
        resultados, imagens = [], []
        for i, ((numero, pag), arq) in enumerate(zip(conteudo, arquivos), 1):
            img = np.array(Image.open(arq))
            x, y, w, h = _area_util(espec, numero)
            altura_px = img.shape[0]
            caixa = (round(x * PX_POR_PT), altura_px - round((y + h) * PX_POR_PT),
                     round((x + w) * PX_POR_PT), altura_px - round(y * PX_POR_PT))
            r = Resultado(i, numero, _rotulo(pag), pag.get("tipo", "desenho"))
            _medir(img, caixa, perfil, r)
            _pontuar(r, perfil)
            resultados.append(r)
            imagens.append(img[caixa[1]:caixa[3], caixa[0]:caixa[2]])

    repetidas = _repeticoes(resultados)
    for a, b, sim in repetidas:
        b.nota = max(0, b.nota - 10)
        b.problemas.append(f"Muito parecida com a página {a.pagina_livro} ({sim:.0%}).")

    media = round(sum(r.nota for r in resultados) / len(resultados))
    _prancha(resultados, imagens, pasta / "qualidade.png")
    (pasta / "qualidade.md").write_text(_relatorio(tema, perfil, resultados, media),
                                        encoding="utf-8")
    return {"media": media, "paginas": len(resultados),
            "abaixo_de_65": sum(r.nota < 65 for r in resultados),
            "relatorio": pasta / "qualidade.md", "prancha": pasta / "qualidade.png"}


def _relatorio(tema, perfil, resultados, media) -> str:
    tipos = {}
    for r in resultados:
        tipos[r.tipo] = tipos.get(r.tipo, 0) + 1
    repetidos = {}
    for p in tema["paginas"]:
        if p.get("tipo", "desenho") == "desenho":
            repetidos[p["desenho"]] = repetidos.get(p["desenho"], 0) + 1
    linhas = [
        f"# Qualidade — {tema['titulo']}",
        "",
        f"**Nota média: {media}/100** · {len(resultados)} páginas de conteúdo · "
        f"régua: {perfil.nome}",
        "",
        "| Faixa | Páginas |",
        "|---|---|",
        f"| 🟢 85 a 100 | {sum(r.nota >= 85 for r in resultados)} |",
        f"| 🟠 65 a 84 | {sum(65 <= r.nota < 85 for r in resultados)} |",
        f"| 🔴 abaixo de 65 | {sum(r.nota < 65 for r in resultados)} |",
        "",
        "**Variedade:** " + ", ".join(f"{n} {t}" for t, n in tipos.items()),
        "",
    ]
    rep = [f"{d} ({n}×)" for d, n in repetidos.items() if n > 1]
    if rep:
        linhas += [f"**Desenhos repetidos no livro:** {', '.join(rep)}", ""]
    linhas += [
        "## Páginas com problemas",
        "",
        "| Pág. | Conteúdo | Nota | Ocupação | Áreas | Pequenas | Traço fino | Problemas |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(resultados, key=lambda r: r.nota):
        if not r.problemas:
            continue
        linhas.append(f"| {r.pagina_livro} | {r.rotulo} | {r.nota} | {r.ocupacao:.0%} | "
                      f"{r.areas} | {r.areas_pequenas} | {r.traco_fino:.0%} | "
                      f"{' '.join(r.problemas)} |")
    sem = [r for r in resultados if not r.problemas]
    linhas += ["", f"**Sem problemas ({len(sem)}):** "
               + (", ".join(f"p.{r.pagina_livro} {r.rotulo}" for r in sem) or "nenhuma"), ""]
    linhas += ["As regras estão em `colorbook/estilo.py`. Ajuste-as com o que observar na "
               "cópia de prova.", ""]
    return "\n".join(linhas)
