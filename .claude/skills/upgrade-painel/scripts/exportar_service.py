#!/usr/bin/env python3
"""Exporta as páginas de um relatório publicado no Power BI Service como PNG/PDF (API REST "Export To File").

Uso: exportar_service.py --workspace <id> --relatorio <id> [--formato PNG|PDF] [--paginas id1,id2] [--saida PASTA]

Requisitos (do lado do Power BI, não deste script):
- Relatório publicado num workspace em capacidade Premium, Embedded ou Fabric (exigência da API ExportTo).
- Token com permissão Report.Read.All. Informe-o na variável PBI_TOKEN ou, numa sessão Claude Code na nuvem,
  cadastre a credencial do host api.powerbi.com no ambiente (o proxy injeta o cabeçalho Authorization).
- Acesso de rede a api.powerbi.com.

ATENÇÃO: não foi possível testar este script contra um tenant real ao criá-lo; valide na primeira execução.
Referência: https://learn.microsoft.com/rest/api/power-bi/reports/export-to-file-in-group
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.powerbi.com/v1.0/myorg"


def req(metodo, url, corpo=None, binario=False):
    h = {"Content-Type": "application/json"}
    if os.environ.get("PBI_TOKEN"):
        h["Authorization"] = "Bearer " + os.environ["PBI_TOKEN"]
    r = urllib.request.Request(url, method=metodo, headers=h,
                               data=json.dumps(corpo).encode() if corpo is not None else None)
    with urllib.request.urlopen(r, timeout=120) as resp:
        dados = resp.read()
        return dados if binario else (json.loads(dados) if dados else {})


def exportar(ws, rel, formato, pagina, saida):
    base = f"{API}/groups/{ws}/reports/{rel}"
    corpo = {"format": formato}
    if pagina:
        corpo["powerBIReportConfiguration"] = {"pages": [{"pageName": pagina}]}
    job = req("POST", f"{base}/ExportTo", corpo)
    jid = job["id"]
    for _ in range(120):
        st = req("GET", f"{base}/exports/{jid}")
        if st.get("status") == "Succeeded":
            ext = st.get("resourceFileExtension", "." + formato.lower())
            arq = saida / f"{pagina or rel}{ext}"
            arq.write_bytes(req("GET", f"{base}/exports/{jid}/file", binario=True))
            return arq
        if st.get("status") == "Failed":
            raise RuntimeError(f"Exportação falhou: {st.get('error')}")
        time.sleep(max(2, int(st.get("retryAfter", 5))))
    raise RuntimeError("Tempo esgotado aguardando a exportação")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--relatorio", required=True)
    ap.add_argument("--formato", default="PNG", choices=["PNG", "PDF"])
    ap.add_argument("--paginas", help="ids das páginas (nome interno); sem isso exporta o relatório todo")
    ap.add_argument("--saida", default="prints_service")
    a = ap.parse_args()
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    paginas = a.paginas.split(",") if a.paginas else [None]
    try:
        for p in paginas:
            print(exportar(a.workspace, a.relatorio, a.formato, p, saida))
    except urllib.error.HTTPError as e:
        sys.exit(f"ERRO HTTP {e.code}: {e.read()[:300]!r} — confira token, permissões e capacidade Premium/Fabric")
    except (urllib.error.URLError, RuntimeError) as e:
        sys.exit(f"ERRO {e}")


if __name__ == "__main__":
    main()
