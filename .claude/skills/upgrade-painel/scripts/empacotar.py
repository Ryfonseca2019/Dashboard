#!/usr/bin/env python3
"""Empacota a nova versão de um painel PBIP no padrão do repositório.

Uso:
  empacotar.py <pasta_do_projeto> --nome Planejamento_SENAI_X --versao 49 [--base <versão anterior>]
               [--leia-me LEIA_ME.txt] [--saida PASTA] [--extra arquivo ...]

- Valida o relatório (pbir_tool validar) e recusa empacotar se houver erro.
- Sem --leia-me, gera LEIA_ME_V<versao>.txt com o changelog automático (comparação com --base).
- Exclui arquivos locais do Desktop (.pbi/localSettings.json, .pbi/cache.abf).
"""
import argparse
import contextlib
import io
import sys
import zipfile
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parents[1] / "pbir-paginas-visuais" / "scripts"))
import analisar_painel as AP  # noqa: E402
import pbir_tool as PT  # noqa: E402

IGNORAR = ("localSettings.json", "cache.abf")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--nome", required=True)
    ap.add_argument("--versao", required=True)
    ap.add_argument("--base")
    ap.add_argument("--leia-me")
    ap.add_argument("--saida", default=".")
    ap.add_argument("--extra", nargs="*", default=[])
    a = ap.parse_args()

    proj = Path(a.projeto).resolve()
    reports = [proj] if proj.name.endswith(".Report") else sorted(proj.glob("*.Report"))
    if not reports:
        sys.exit(f"ERRO  nenhuma pasta *.Report em {proj}")
    raiz = reports[0].parent
    for rep in reports:
        r, m = PT.localizar(str(rep))
        problemas = PT.validar(r, m)
        erros = [x for n, x in problemas if n == "ERRO"]
        if erros:
            print("\n".join(f"ERRO  {e}" for e in erros))
            sys.exit("Empacotamento cancelado: corrija os erros de validação.")

    if a.leia_me:
        leia = Path(a.leia_me).read_text(encoding="utf-8")
    else:
        mudancas = ""
        if a.base:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                AP.comparar(a.base, str(raiz))
            mudancas = buf.getvalue()
        leia = (f"V{a.versao} — {a.nome} ({date.today():%d/%m/%Y})\n\n"
                "1. Extraia o ZIP em uma pasta nova.\n"
                "2. Abra o arquivo .pbip no Power BI Desktop, na rede corporativa, e clique em Atualizar.\n"
                "3. Confira as páginas novas/alteradas listadas abaixo.\n\n"
                "O que mudou:\n" + (mudancas or "(descrever)\n") +
                "\nValidação estática: estrutura PBIR, referências de campos e schema oficial conferidos.\n"
                "Renderização, medidas DAX novas e dados reais dependem da atualização no Desktop.\n")
    destino = Path(a.saida).resolve() / f"{a.nome}_v{a.versao}.zip"
    destino.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(raiz.rglob("*")):
            if f.is_file() and f.name not in IGNORAR and destino != f:
                z.write(f, f.relative_to(raiz).as_posix())
                n += 1
        z.writestr(f"LEIA_ME_V{a.versao}.txt", leia)
        for e in a.extra:
            z.write(e, Path(e).name)
    print(f"{destino} ({n} arquivos + LEIA_ME_V{a.versao}.txt)")


if __name__ == "__main__":
    main()
