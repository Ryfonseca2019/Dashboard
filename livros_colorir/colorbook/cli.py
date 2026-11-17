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
from .capa import gerar_capa, gerar_miniaturas
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
    from .colecao import outros_volumes

    espec = gerar_capa(tema, paginas, capa, outros_volumes(tema, arquivo_tema.parent))
    miniaturas = gerar_miniaturas(capa, espec)
    anuncio = gerar_anuncio(tema, paginas, espec, pasta)
    problemas = validar(tema, miolo, capa, espec)

    print(f"\n📘 {tema['titulo']}")
    print(f"   Miolo:   {miolo}  ({paginas} páginas)")
    print(f"   Capa:    {capa}  ({espec.largura_total:.3f} × {espec.altura_total:.3f} pol, "
          f"lombada {espec.lombada:.3f} pol)")
    print(f"   Anúncio: {pasta / 'anuncio.md'}")
    if miniaturas:
        print(f"   Prévia da capa: {miniaturas[0]} (miniatura da busca: {miniaturas[1].name})")
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

    rv = sub.add_parser("revisar", help="revisão estética de cada página com a visão do Claude")
    rv.add_argument("temas", type=Path, nargs="*", help="temas (padrão: todos de temas/)")
    rv.add_argument("--saida", type=Path, default=RAIZ / "saida")
    rv.add_argument("--simular", action="store_true",
                    help="não chama a API: só conta as páginas e estima o custo")

    pi = sub.add_parser("pedidos-ilustracao",
                        help="gera os pedidos (prompts) para uma ferramenta de imagens")
    pi.add_argument("tema", type=Path)
    pi.add_argument("--pular-pasta", type=Path,
                    help="pasta com imagens já prontas (esses desenhos ficam de fora)")
    pi.add_argument("--lote", type=int, default=0, help="agrupa os pedidos em lotes de N")
    pi.add_argument("--saida", type=Path, default=RAIZ / "saida")

    ii = sub.add_parser("importar-ilustracoes",
                        help="limpa imagens geradas e cria um tema que as usa")
    ii.add_argument("pasta", type=Path)
    ii.add_argument("tema", type=Path)

    f = sub.add_parser("folha-teste", help="gera a folha de teste de impressão (PROVA.md)")
    f.add_argument("--saida", type=Path, default=RAIZ / "saida")

    q = sub.add_parser("auditar", help="mede a qualidade das páginas e dá nota de 0 a 100")
    q.add_argument("temas", type=Path, nargs="*", help="temas (padrão: todos de temas/)")
    q.add_argument("--saida", type=Path, default=RAIZ / "saida")

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
    elif a.cmd == "auditar":
        from .auditar import auditar

        for arq in a.temas or sorted((RAIZ / "temas").glob("*.json")):
            r = auditar(arq, a.saida)
            print(f"📊 {arq.stem}: nota média {r['media']}/100 · {r['paginas']} páginas · "
                  f"{r['abaixo_de_65']} abaixo de 65")
            print(f"   Relatório: {r['relatorio']}")
            print(f"   Prévia:    {r['prancha']}")
    elif a.cmd == "revisar":
        from .claude_cliente import AJUDA_CHAVE
        from .revisar import revisar

        for arq in a.temas or sorted((RAIZ / "temas").glob("*.json")):
            r = revisar(arq, a.saida, simular=a.simular)
            if r["simulado"]:
                print(f"🔎 {arq.stem}: {r['paginas']} páginas · custo estimado "
                      f"US$ {r['custo_estimado_usd']:.2f} (simulação, nada foi enviado)")
                if r["sem_chave"] and not a.simular:
                    print(AJUDA_CHAVE)
            else:
                print(f"🎨 {arq.stem}: nota visual média {r['media']:.1f}/10 · "
                      f"{r['abaixo_de_7']} abaixo de 7 · {r['nao_reconhecidas']} não reconhecidas")
                print(f"   Relatório: {r['relatorio']}")
    elif a.cmd == "pedidos-ilustracao":
        from .ilustracoes import gerar_pedidos

        prontos = ({f.stem for f in a.pular_pasta.iterdir()}
                   if a.pular_pasta and a.pular_pasta.is_dir() else set())
        print(f"Pedidos: {gerar_pedidos(a.tema, a.saida, prontos, a.lote)}")
    elif a.cmd == "importar-ilustracoes":
        from .ilustracoes import importar

        novo, trocadas = importar(a.pasta, a.tema)
        for t in trocadas:
            print(f"   🖼️  {t}")
        print(f"Tema com as ilustrações: {novo}")
        print(f"Gere o livro com: python -m colorbook construir {novo}")
    elif a.cmd == "folha-teste":
        from .folha_teste import gerar_folha_teste

        a.saida.mkdir(parents=True, exist_ok=True)
        print(f"Folha de teste: {gerar_folha_teste(a.saida / 'folha_teste.pdf')}")
    elif a.cmd == "desenhos":
        print("\n".join(sorted(DESENHOS)))
    elif a.cmd == "criar-tema":
        from .claude_tema import criar_tema

        arquivo = criar_tema(a.ideia, a.autor, a.temas)
        print(f"Tema criado: {arquivo}")
        if a.construir:
            sys.exit(0 if construir(arquivo, a.saida) else 1)
