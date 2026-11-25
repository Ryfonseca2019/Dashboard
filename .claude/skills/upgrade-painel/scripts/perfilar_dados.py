#!/usr/bin/env python3
"""Perfil de dados exportados do painel (CSV/XLSX) para orientar a escolha de visuais e escrever
títulos de ação com números reais (Storytelling com Dados, L6).

Uso: perfilar_dados.py <arquivo.csv|.xlsx|pasta> [--saida perfil.json]

Para cada coluna: tipo, valores distintos, % nulos, mín/máx/média, atípicos (regra 1,5×IQR) e valores
mais frequentes. Para cada par categoria × número: concentração (participação das 3 maiores) e líder.
O resultado alimenta `analisar_painel.py analisar ... --dados perfil.json`.

Como obter os CSVs: em cada visual, "Mais opções (…) › Exportar dados", ou exportações já usadas nas entregas.
"""
import argparse
import csv
import io
import json
import re
import statistics
import sys
from pathlib import Path


def ler_texto(p: Path):
    b = p.read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", "replace")


def ler_csv(p: Path):
    txt = ler_texto(p)
    try:
        dial = csv.Sniffer().sniff(txt[:5000], delimiters=";,\t|")
    except csv.Error:
        dial = csv.excel
        dial.delimiter = ";" if txt[:2000].count(";") > txt[:2000].count(",") else ","
    linhas = list(csv.reader(io.StringIO(txt), dial))
    if not linhas:
        return [], []
    return linhas[0], linhas[1:]


def ler_xlsx(p: Path):
    try:
        import openpyxl
    except ImportError:
        print(f"AVISO {p.name}: openpyxl ausente; exporte como CSV", file=sys.stderr)
        return []
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    tabelas = []
    for ws in wb.worksheets:
        dados = [["" if c is None else str(c) for c in r] for r in ws.iter_rows(values_only=True)]
        dados = [r for r in dados if any(x.strip() for x in r)]
        if len(dados) > 1:
            tabelas.append((f"{p.stem}::{ws.title}", dados[0], dados[1:]))
    return tabelas


RE_NUM = re.compile(r"^-?[\d.\s]*,?\d+%?$|^-?\d+(\.\d+)?%?$")


def numero(s):
    s = (s or "").strip().replace("R$", "").replace(" ", "").strip()
    if not s or not RE_NUM.match(s.replace(" ", "")):
        return None
    pct = s.endswith("%")
    s = s.rstrip("%").replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return None
    return v / 100 if pct else v


def perfil_tabela(nome, cab, linhas):
    cols = []
    n = len(linhas)
    for i, c in enumerate(cab):
        vals = [(r[i] if i < len(r) else "").strip() for r in linhas]
        nao_nulos = [v for v in vals if v and v.lower() not in ("null", "(em branco)", "(blank)", "nan")]
        nums = [numero(v) for v in nao_nulos]
        e_num = nao_nulos and sum(x is not None for x in nums) / len(nao_nulos) >= 0.9
        info = {"coluna": c, "linhas": n, "nulos_pct": round(100 * (1 - len(nao_nulos) / n), 1) if n else 0,
                "distintos": len(set(nao_nulos))}
        if e_num:
            xs = sorted(x for x in nums if x is not None)
            info.update(tipo="numero", min=xs[0], max=xs[-1], media=round(statistics.fmean(xs), 4),
                        soma=round(sum(xs), 4))
            if len(xs) >= 8:
                q1, _, q3 = statistics.quantiles(xs, n=4)
                iqr = q3 - q1
                fora = [x for x in xs if x < q1 - 1.5 * iqr or x > q3 + 1.5 * iqr]
                info["atipicos"] = len(fora)
        else:
            freq = {}
            for v in nao_nulos:
                freq[v] = freq.get(v, 0) + 1
            info.update(tipo="texto", mais_frequentes=sorted(freq.items(), key=lambda kv: -kv[1])[:5])
        cols.append(info)
    insights = []
    cats = [c for c in cols if c["tipo"] == "texto" and 2 <= c["distintos"] <= 60]
    nao_somavel = re.compile(r"((^|_|\s)(cod|codigo|id|status|filial|coligada|ano|mes|dia|hora|nivel|tipo|"
                             r"ordem|sequencia|cpf|cnpj|cep|telefone)(_|\s|$))|(^cod)|(ID$)", re.I)
    nums = [c for c in cols if c["tipo"] == "numero" and c["distintos"] > 1 and not nao_somavel.search(c["coluna"])]
    cats = [c for c in cats if not re.search(r"(^|_)(hora|data)", c["coluna"], re.I)]
    for cat in cats[:3]:
        ic = cab.index(cat["coluna"])
        for num in nums[:4]:
            iv = cab.index(num["coluna"])
            soma = {}
            for r in linhas:
                k = (r[ic] if ic < len(r) else "").strip()
                v = numero(r[iv] if iv < len(r) else "")
                if k and v is not None:
                    soma[k] = soma.get(k, 0) + v
            tot = sum(soma.values())
            if len(soma) < 2 or not tot or any(v < 0 for v in soma.values()):
                continue
            ordem = sorted(soma.items(), key=lambda kv: -kv[1])
            top3 = sum(v for _, v in ordem[:3]) / tot
            lider, vl = ordem[0]
            frase = (f"{lider} lidera {num['coluna']} com {vl / tot:.0%} do total" if len(ordem) <= 3 else
                     f"As 3 maiores {cat['coluna']} ({', '.join(k for k, _ in ordem[:3])}) concentram "
                     f"{top3:.0%} de {num['coluna']}")
            insights.append({"categoria": cat["coluna"], "medida": num["coluna"], "categorias": len(ordem),
                             "lider": lider, "participacao_lider": round(vl / tot, 4),
                             "participacao_top3": round(top3, 4), "manchete": frase})
    return {"tabela": nome, "linhas": n, "colunas": cols, "insights": insights}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada")
    ap.add_argument("--saida", default="perfil.json")
    a = ap.parse_args()
    p = Path(a.entrada)
    arquivos = sorted(x for x in (p.rglob("*") if p.is_dir() else [p]) if x.suffix.lower() in (".csv", ".xlsx"))
    resultado = []
    for f in arquivos:
        if f.suffix.lower() == ".csv":
            cab, linhas = ler_csv(f)
            if cab:
                resultado.append(perfil_tabela(f.stem, cab, linhas))
        else:
            for nome, cab, linhas in ler_xlsx(f):
                resultado.append(perfil_tabela(nome, cab, linhas))
    Path(a.saida).write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    for t in resultado:
        print(f"{t['tabela']}: {t['linhas']} linhas, {len(t['colunas'])} colunas, {len(t['insights'])} manchete(s)")
        for i in t["insights"][:3]:
            print(f"   • {i['manchete']}")
    print(f"→ {a.saida}")


if __name__ == "__main__":
    main()
