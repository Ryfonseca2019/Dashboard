#!/usr/bin/env python3
"""Converte o PDF exportado do Power BI (Arquivo › Exportar › PDF) em uma imagem PNG por página,
para avaliar o painel renderizado (cores reais, legibilidade, visuais vazios, rótulos cortados).

Uso: paginas_pdf.py <arquivo.pdf> [--saida PASTA] [--dpi 110]
Requer pdftoppm (poppler-utils).
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--saida")
    ap.add_argument("--dpi", type=int, default=110)
    a = ap.parse_args()
    if not shutil.which("pdftoppm"):
        sys.exit("ERRO  pdftoppm não encontrado (instale poppler-utils)")
    pdf = Path(a.pdf).resolve()
    saida = Path(a.saida or pdf.with_suffix("")).resolve()
    saida.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftoppm", "-png", "-r", str(a.dpi), str(pdf), str(saida / "pagina")], check=True)
    imgs = sorted(saida.glob("pagina*.png"))
    for i in imgs:
        print(i)
    print(f"{len(imgs)} página(s) em {saida}")


if __name__ == "__main__":
    main()
