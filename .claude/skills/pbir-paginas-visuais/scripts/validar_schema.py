#!/usr/bin/env python3
"""Valida os JSON do relatório (PBIR) contra os schemas oficiais da Microsoft.

Uso: validar_schema.py <pasta do projeto ou *.Report> [trecho_de_caminho ...]
Os trechos opcionais limitam a validação (ex.: o id da página nova).
Os schemas são baixados do espelho no GitHub (microsoft/json-schemas) e guardados em ~/.cache/pbir-schemas.
Requer: pip install jsonschema
"""
import json
import pathlib
import re
import sys
import urllib.request

from jsonschema import Draft7Validator, Draft202012Validator
from referencing import Registry, Resource

CACHE = pathlib.Path.home() / ".cache" / "pbir-schemas"
OFICIAL = "https://developer.microsoft.com/json-schemas/"
ESPELHO = "https://raw.githubusercontent.com/microsoft/json-schemas/main/"


def buscar(uri):
    CACHE.mkdir(parents=True, exist_ok=True)
    local = CACHE / re.sub(r"[^A-Za-z0-9.]", "_", uri)
    if not local.exists():
        local.write_bytes(urllib.request.urlopen(uri.replace(OFICIAL, ESPELHO), timeout=30).read())
    return Resource.from_contents(json.loads(local.read_text(encoding="utf-8-sig")))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    raiz = pathlib.Path(sys.argv[1]).resolve()
    filtros = sys.argv[2:]
    registro = Registry(retrieve=buscar)
    total = falhas = 0
    sem_schema = set()
    for arq in sorted(raiz.rglob("*.json")):
        if filtros and not any(f in str(arq) for f in filtros):
            continue
        dados = json.loads(arq.read_text(encoding="utf-8-sig"))
        uri = dados.get("$schema") if isinstance(dados, dict) else None
        if not uri or "/report/definition/" not in uri:
            continue
        try:
            schema = buscar(uri).contents
        except Exception as e:  # schema ausente no espelho ou sem rede
            if uri not in sem_schema:
                print(f"AVISO schema indisponível, arquivos com ele não foram validados: {uri} ({e})")
            sem_schema.add(uri)
            continue
        V = Draft202012Validator if "2020-12" in schema.get("$schema", "") else Draft7Validator
        erros = list(V(schema, registry=registro).iter_errors(dados))
        total += 1
        if erros:
            falhas += 1
            for e in erros[:5]:
                caminho = "/".join(str(p) for p in e.absolute_path)
                print(f"FALHA {arq.relative_to(raiz)} [{caminho}] {e.message[:200]}")
    print(f"\nSchema: {total} arquivo(s) validado(s), {falhas} com falha")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
