"""Linha de comando.

  python -m colorbook construir temas/primeiros_desenhos.json
  python -m colorbook construir-todos
  python -m colorbook previa saida/primeiros_desenhos
  python -m colorbook desenhos
  python -m colorbook criar-tema "dinossauros fofos para 3 a 6 anos" --autor "Seu Nome"
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from .anuncio import gerar_anuncio
from .capa import gerar_capa
from .desenhos import DESENHOS
from .miolo import gerar_miolo
from .validar import validar

RAIZ = Path(__file__).resolve().parent.parent


def construir(arquivo_tema: Path, saida: Path) -> bool:
    tema = json.loads(arquivo_tema.read_text(encoding="utf-8"))
    pasta = saida / tema.get("id", arquivo_tema.stem)
    pasta.mkdir(parents=True, exist_ok=True)
    miolo = pasta / "miolo.pdf"
    capa = pasta / "capa.pdf"

    paginas = gerar_miolo(tema, miolo, base=arquivo_tema.parent)
    espec = gerar_capa(tema, paginas, capa)
    anuncio = gerar_anuncio(tema, paginas, espec, pasta)
    problemas = validar(tema, miolo, capa, espec)

    print(f"\n📘 {tema['titulo']}")
    print(f"   Miolo:   {miolo}  ({paginas} páginas)")
    print(f"   Capa:    {capa}  ({espec.largura_total:.3f} × {espec.altura_total:.3f} pol, "
          f"lombada {espec.lombada:.3f} pol)")
    print(f"   Anúncio: {pasta / 'anuncio.md'}")
    for aviso in anuncio["avisos"]:
        print(f"   ⚠️  {aviso}")
    if problemas:
        for p in problemas:
            print(f"   ❌ {p}")
        return False
    print("   ✅ Pronto para enviar ao KDP")
    return True


def previa(pasta: Path, paginas: str) -> None:
    """Gera PNGs para conferir as páginas (precisa do pdftoppm / poppler)."""
    if not shutil.which("pdftoppm"):
        sys.exit("Instale o poppler (pdftoppm) para gerar prévias.")
    destino = pasta / "previa"
    destino.mkdir(exist_ok=True)
    inicio, _, fim = paginas.partition("-")
    subprocess.run(["pdftoppm", "-png", "-r", "40", "-f", inicio, "-l", fim or inicio,
                    str(pasta / "miolo.pdf"), str(destino / "miolo")], check=True)
    subprocess.run(["pdftoppm", "-png", "-r", "30", str(pasta / "capa.pdf"),
                    str(destino / "capa")], check=True)
    print(f"Prévias em {destino}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="colorbook", description="Fábrica de livros de colorir")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("construir", help="gera miolo, capa e anúncio de um tema")
    c.add_argument("tema", type=Path)
    c.add_argument("--saida", type=Path, default=RAIZ / "saida")

    t = sub.add_parser("construir-todos", help="gera todos os temas da pasta temas/")
    t.add_argument("--temas", type=Path, default=RAIZ / "temas")
    t.add_argument("--saida", type=Path, default=RAIZ / "saida")

    p = sub.add_parser("previa", help="gera imagens PNG para conferir o livro")
    p.add_argument("pasta", type=Path)
    p.add_argument("--paginas", default="1-12", help="intervalo, ex.: 1-12")

    sub.add_parser("desenhos", help="lista os desenhos disponíveis")

    n = sub.add_parser("criar-tema", help="usa a API do Claude para criar um tema novo")
    n.add_argument("ideia")
    n.add_argument("--autor", default="")
    n.add_argument("--temas", type=Path, default=RAIZ / "temas")
    n.add_argument("--construir", action="store_true", help="já gera o livro em seguida")
    n.add_argument("--saida", type=Path, default=RAIZ / "saida")

    a = ap.parse_args(argv)
    if a.cmd == "construir":
        sys.exit(0 if construir(a.tema, a.saida) else 1)
    elif a.cmd == "construir-todos":
        resultados = [construir(f, a.saida) for f in sorted(a.temas.glob("*.json"))]
        sys.exit(0 if all(resultados) else 1)
    elif a.cmd == "previa":
        previa(a.pasta, a.paginas)
    elif a.cmd == "desenhos":
        print("\n".join(sorted(DESENHOS)))
    elif a.cmd == "criar-tema":
        from .claude_tema import criar_tema

        arquivo = criar_tema(a.ideia, a.autor, a.temas)
        print(f"Tema criado: {arquivo}")
        if a.construir:
            sys.exit(0 if construir(arquivo, a.saida) else 1)
