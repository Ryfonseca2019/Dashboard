#!/usr/bin/env python3
"""Ferramenta para evoluir relatórios Power BI em formato PBIP/PBIR.

Comandos:
  campos  <projeto> [--busca TEXTO] [--tabela NOME]   lista tabelas, colunas e medidas do modelo (TMDL)
  criar   <projeto> <spec.json> [--simular]            cria página nova ou adiciona visuais a uma página existente
  validar <projeto>                                    confere estrutura, IDs e referências de campos

<projeto> pode ser a pasta que contém o .pbip, a pasta *.Report ou o próprio arquivo .pbip.
"""
import argparse
import json
import re
import secrets
import sys
from collections import Counter
from pathlib import Path

SCHEMA_BASE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
SCHEMA_VISUAL_PADRAO = f"{SCHEMA_BASE}/visualContainer/2.12.0/schema.json"
SCHEMA_PAGINA_PADRAO = f"{SCHEMA_BASE}/page/2.1.0/schema.json"

# Paleta já usada nos painéis (Produtividade / Planejamento de Turmas)
COR_TITULO = "#163B65"
COR_VALOR = "#0072CE"
COR_FUNDO_PAGINA = "#F3F6FA"
COR_FUNDO_VISUAL = "#FFFFFF"
COR_BORDA = "#E6E6E6"

# Papéis (buckets) aceitos por tipo de visual
PAPEIS = {
    "card": ["Values"],
    "slicer": ["Values"],
    "tableEx": ["Values"],
    "pivotTable": ["Rows", "Columns", "Values"],
    "clusteredBarChart": ["Category", "Y", "Series", "Tooltips"],
    "clusteredColumnChart": ["Category", "Y", "Series", "Tooltips"],
    "lineChart": ["Category", "Y", "Series", "Tooltips"],
    "donutChart": ["Category", "Y", "Tooltips"],
    "textbox": [],
}
APELIDOS = {"cartao": "card", "segmentacao": "slicer", "tabela": "tableEx", "matriz": "pivotTable",
            "barras": "clusteredBarChart", "colunas": "clusteredColumnChart", "linha": "lineChart",
            "rosca": "donutChart", "texto": "textbox", "titulo": "textbox"}


class Erro(Exception):
    pass


# --------------------------------------------------------------------------- localização
def localizar(projeto: str):
    p = Path(projeto).resolve()
    if p.is_file() and p.suffix == ".pbip":
        p = p.parent
    if p.name.endswith(".Report") and p.is_dir():
        report = p
    else:
        candidatos = sorted(p.glob("*.Report"))
        if not candidatos:
            candidatos = sorted(p.glob("**/*.Report"))
        if len(candidatos) != 1:
            raise Erro(f"Esperava exatamente uma pasta *.Report em {p}, encontrei {len(candidatos)}: "
                       + ", ".join(str(c) for c in candidatos))
        report = candidatos[0]
    pbir = report / "definition.pbir"
    modelo = None
    if pbir.exists():
        ref = ler_json(pbir).get("datasetReference", {}).get("byPath", {}).get("path")
        if ref:
            modelo = (report / ref).resolve()
    if modelo is None or not modelo.exists():
        alt = report.parent / (report.name[: -len(".Report")] + ".SemanticModel")
        modelo = alt if alt.exists() else None
    return report, modelo


def ler_json(caminho: Path):
    try:
        return json.loads(caminho.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise Erro(f"JSON inválido em {caminho}: {e}")


def gravar_json(caminho: Path, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- modelo TMDL
_NOME = r"(?:'((?:[^']|'')+)'|([^\s=']+))"
RE_TABELA = re.compile(rf"^table\s+{_NOME}")
RE_COLUNA = re.compile(rf"^(?:\t|    )column\s+{_NOME}")
RE_MEDIDA = re.compile(rf"^(?:\t|    )measure\s+{_NOME}")


def _nome(m):
    return (m.group(1) or m.group(2)).replace("''", "'")


def ler_modelo(modelo: Path):
    """Retorna {tabela: {"colunas": set, "medidas": set}}."""
    tabelas = {}
    if modelo is None:
        return tabelas
    for arq in sorted((modelo / "definition").rglob("*.tmdl")):
        atual = None
        for linha in arq.read_text(encoding="utf-8-sig").splitlines():
            m = RE_TABELA.match(linha)
            if m:
                atual = tabelas.setdefault(_nome(m), {"colunas": set(), "medidas": set()})
                continue
            if linha and not linha[0].isspace():
                atual = None  # outro objeto de nível superior (relationship, expression...)
                continue
            if atual is None:
                continue
            m = RE_COLUNA.match(linha)
            if m:
                atual["colunas"].add(_nome(m))
                continue
            m = RE_MEDIDA.match(linha)
            if m:
                atual["medidas"].add(_nome(m))
    return tabelas


RE_REF = re.compile(r"^\s*'?(.+?)'?\s*\[(.+)\]\s*$")


def resolver_campo(ref: str, tabelas):
    m = RE_REF.match(ref)
    if not m:
        raise Erro(f"Campo '{ref}' fora do formato Tabela[Campo]")
    tabela, campo = m.group(1), m.group(2)
    if tabela not in tabelas:
        raise Erro(f"Tabela '{tabela}' não existe no modelo (campo {ref}). Use o comando 'campos'.")
    if campo in tabelas[tabela]["medidas"]:
        return "Measure", tabela, campo
    if campo in tabelas[tabela]["colunas"]:
        return "Column", tabela, campo
    raise Erro(f"Campo '{campo}' não existe na tabela '{tabela}'. Use: campos <projeto> --tabela \"{tabela}\"")


# --------------------------------------------------------------------------- construção de JSON
def lit(valor):
    return {"expr": {"Literal": {"Value": valor}}}


def cor(hexa):
    return {"solid": {"color": lit(f"'{hexa}'")}}


def texto(s):
    return lit("'" + s.replace("'", "''") + "'")


def num(n):
    return lit(f"{n}D")


def projecao(tipo, tabela, campo):
    return {
        "field": {tipo: {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": campo}},
        "queryRef": f"{tabela}.{campo}",
        "nativeQueryRef": campo,
    }


def container_objects(titulo, padding):
    objs = {
        "title": [{"properties": {
            "text": texto(titulo or ""), "show": lit("true" if titulo else "false"),
            "titleWrap": lit("true"), "fontColor": cor(COR_TITULO), "fontSize": num(12)}}],
        "background": [{"properties": {"show": lit("true"), "color": cor(COR_FUNDO_VISUAL),
                                       "transparency": num(0)}}],
        "padding": [{"properties": {k: num(v) for k, v in padding.items()}}],
        "border": [{"properties": {"show": lit("false"), "color": cor(COR_BORDA),
                                   "radius": num(8), "width": num(1)}}],
        "dropShadow": [{"properties": {"show": lit("false")}}],
        "visualHeader": [{"properties": {"show": lit("true")}}],
    }
    return objs


def montar_visual(spec, nome, z, schema, tabelas):
    tipo = APELIDOS.get(spec["tipo"], spec["tipo"])
    if tipo not in PAPEIS:
        raise Erro(f"Tipo de visual '{spec['tipo']}' não suportado. Use: {', '.join(PAPEIS)}")
    pos = spec.get("posicao") or {}
    for k in ("x", "y", "largura", "altura"):
        if k not in pos:
            raise Erro(f"Visual '{spec.get('titulo', tipo)}': posicao.{k} obrigatório")
    visual = {"visualType": tipo}

    campos = spec.get("campos", {})
    if tipo != "textbox":
        if not campos:
            raise Erro(f"Visual '{spec.get('titulo', tipo)}' ({tipo}) sem campos")
        estado = {}
        for papel, refs in campos.items():
            if papel not in PAPEIS[tipo]:
                raise Erro(f"Papel '{papel}' inválido para {tipo}. Aceitos: {PAPEIS[tipo]}")
            if isinstance(refs, str):
                refs = [refs]
            estado[papel] = {"projections": [projecao(*resolver_campo(r, tabelas)) for r in refs]}
        visual["query"] = {"queryState": estado}

    objetos = {}
    if tipo == "card":
        objetos = {"labels": [{"properties": {"fontSize": num(spec.get("tamanho_valor", 27)),
                                              "labelDisplayUnits": num(0), "color": cor(COR_VALOR)}}],
                   "categoryLabels": [{"properties": {"show": lit("false")}}]}
        padding = {"top": 8, "bottom": 8, "left": 8, "right": 8}
    elif tipo == "slicer":
        objetos = {"data": [{"properties": {"mode": texto(spec.get("modo", "Dropdown"))}}],
                   "header": [{"properties": {"show": lit("false")}}]}
        padding = {"top": 0, "bottom": 0, "left": 0, "right": 0}
    elif tipo in ("clusteredBarChart", "clusteredColumnChart", "lineChart", "donutChart"):
        objetos = {"labels": [{"properties": {"show": lit("true"), "labelDisplayUnits": num(1)}}]}
        padding = {"top": 14, "bottom": 16, "left": 16, "right": 16}
    elif tipo == "textbox":
        conteudo = spec.get("texto") or spec.get("titulo") or ""
        tamanho = spec.get("tamanho_fonte", "24pt")
        objetos = {"general": [{"properties": {"paragraphs": [{"textRuns": [{
            "value": conteudo,
            "textStyle": {"fontFamily": "Segoe UI", "fontSize": tamanho, "color": COR_TITULO}}]}]}}]}
        padding = {"top": 4, "bottom": 4, "left": 8, "right": 8}
    else:
        padding = {"top": 8, "bottom": 8, "left": 8, "right": 8}
    if objetos:
        visual["objects"] = objetos
    titulo = None if tipo == "textbox" else spec.get("titulo")
    visual["visualContainerObjects"] = container_objects(titulo, padding)
    visual["drillFilterOtherVisuals"] = True

    return {
        "$schema": schema,
        "name": nome,
        "position": {"x": pos["x"], "y": pos["y"], "width": pos["largura"], "height": pos["altura"],
                     "z": z, "tabOrder": z},
        "visual": visual,
    }


# --------------------------------------------------------------------------- utilidades do relatório
def schema_mais_usado(pasta_paginas: Path, arquivo, padrao):
    cont = Counter()
    for f in pasta_paginas.rglob(arquivo):
        try:
            s = ler_json(f).get("$schema")
        except Erro:
            continue
        if s:
            cont[s] += 1
    return cont.most_common(1)[0][0] if cont else padrao


def ids_existentes(pasta_paginas: Path):
    return {p.name for p in pasta_paginas.rglob("*") if p.is_dir()}


def novo_id(usados):
    while True:
        i = secrets.token_hex(10)
        if i not in usados:
            usados.add(i)
            return i


# --------------------------------------------------------------------------- comandos
def cmd_campos(args):
    _, modelo = localizar(args.projeto)
    tabelas = ler_modelo(modelo)
    if not tabelas:
        raise Erro("Nenhuma tabela encontrada no modelo semântico.")
    busca = (args.busca or "").lower()
    for nome in sorted(tabelas):
        if args.tabela and nome != args.tabela:
            continue
        t = tabelas[nome]
        cols = sorted(c for c in t["colunas"] if busca in c.lower() or busca in nome.lower())
        meds = sorted(m for m in t["medidas"] if busca in m.lower() or busca in nome.lower())
        if busca and not cols and not meds:
            continue
        print(f"\n{nome}  ({len(t['colunas'])} colunas, {len(t['medidas'])} medidas)")
        for m in meds:
            print(f"  [medida] {nome}[{m}]")
        for c in cols:
            print(f"  [coluna] {nome}[{c}]")


def cmd_criar(args):
    report, modelo = localizar(args.projeto)
    tabelas = ler_modelo(modelo)
    spec = ler_json(Path(args.spec))
    paginas_dir = report / "definition" / "pages"
    pages_json = paginas_dir / "pages.json"
    meta = ler_json(pages_json) if pages_json.exists() else {
        "$schema": f"{SCHEMA_BASE}/pagesMetadata/1.1.0/schema.json", "pageOrder": []}
    usados = ids_existentes(paginas_dir)
    schema_visual = schema_mais_usado(paginas_dir, "visual.json", SCHEMA_VISUAL_PADRAO)
    schema_pagina = schema_mais_usado(paginas_dir, "page.json", SCHEMA_PAGINA_PADRAO)

    pspec = spec.get("pagina", {})
    alvo = pspec.get("existente")
    gravacoes = []
    if alvo:
        # adicionar visuais em página existente (por id ou displayName)
        pagina_dir = paginas_dir / alvo
        if not pagina_dir.exists():
            achou = [d for d in paginas_dir.iterdir() if d.is_dir() and (d / "page.json").exists()
                     and ler_json(d / "page.json").get("displayName") == alvo]
            if len(achou) != 1:
                raise Erro(f"Página existente '{alvo}' não encontrada (use o id da pasta ou o displayName exato)")
            pagina_dir = achou[0]
        pagina = ler_json(pagina_dir / "page.json")
        z = 1 + max([ler_json(f).get("position", {}).get("z", 0)
                     for f in pagina_dir.glob("visuals/*/visual.json")] or [-1])
        print(f"Adicionando visuais à página existente '{pagina.get('displayName')}' ({pagina_dir.name})")
    else:
        nome_exibicao = pspec.get("nome")
        if not nome_exibicao:
            raise Erro("Informe pagina.nome (página nova) ou pagina.existente")
        for d in paginas_dir.iterdir() if paginas_dir.exists() else []:
            if (d / "page.json").exists() and ler_json(d / "page.json").get("displayName") == nome_exibicao:
                raise Erro(f"Já existe página com o nome '{nome_exibicao}' ({d.name}). "
                           "Use pagina.existente para adicionar visuais a ela.")
        pid = novo_id(usados)
        pagina_dir = paginas_dir / pid
        pagina = {"$schema": schema_pagina, "name": pid, "displayName": nome_exibicao,
                  "displayOption": pspec.get("ajuste", "FitToPage"),
                  "height": pspec.get("altura", 1100), "width": pspec.get("largura", 1440)}
        fundo = pspec.get("fundo", COR_FUNDO_PAGINA)
        if fundo:
            pagina["objects"] = {"background": [{"properties": {"color": cor(fundo), "transparency": num(0)}}]}
        gravacoes.append((pagina_dir / "page.json", pagina))
        z = 0
        ordem = list(meta.get("pageOrder", []))
        depois = pspec.get("depois_de")
        if depois and depois in ordem:
            ordem.insert(ordem.index(depois) + 1, pid)
        else:
            ordem.append(pid)
        meta["pageOrder"] = ordem
        if pspec.get("ativa"):
            meta["activePageName"] = pid
        gravacoes.append((pages_json, meta))

    largura, altura = pagina.get("width", 1440), pagina.get("height", 1100)
    for vs in spec.get("visuais", []):
        vid = novo_id(usados)
        v = montar_visual(vs, vid, z, schema_visual, tabelas)
        p = v["position"]
        if p["x"] < 0 or p["y"] < 0 or p["x"] + p["width"] > largura or p["y"] + p["height"] > altura:
            raise Erro(f"Visual '{vs.get('titulo', vs['tipo'])}' sai da página ({largura}x{altura}): {p}")
        gravacoes.append((pagina_dir / "visuals" / vid / "visual.json", v))
        z += 1

    for caminho, dados in gravacoes:
        rel = caminho.relative_to(report)
        if args.simular:
            print(f"[simulação] gravaria {rel}")
        else:
            gravar_json(caminho, dados)
            print(f"gravado {rel}")
    if not args.simular:
        problemas = validar(report, modelo)
        imprimir_problemas(problemas)
        if any(n == "ERRO" for n, _ in problemas):
            sys.exit(1)


def validar(report: Path, modelo):
    problemas = []

    def erro(msg):
        problemas.append(("ERRO", msg))

    def aviso(msg):
        problemas.append(("AVISO", msg))

    tabelas = ler_modelo(modelo)
    if modelo is None:
        aviso("Modelo semântico não localizado: referências de campos não conferidas")
    paginas_dir = report / "definition" / "pages"
    for f in report.rglob("*.json"):
        try:
            ler_json(f)
        except Erro as e:
            erro(str(e))
    pages_json = paginas_dir / "pages.json"
    if not pages_json.exists():
        erro("definition/pages/pages.json ausente")
        return problemas
    meta = ler_json(pages_json)
    ordem = meta.get("pageOrder", [])
    pastas = sorted(d.name for d in paginas_dir.iterdir() if d.is_dir())
    for pid, n in Counter(ordem).items():
        if n > 1:
            erro(f"pageOrder repete a página {pid}")
    for pid in ordem:
        if pid not in pastas:
            erro(f"pageOrder cita {pid}, mas a pasta não existe")
    for pid in pastas:
        if pid not in ordem:
            erro(f"Pasta de página {pid} não está em pageOrder")
    if meta.get("activePageName") and meta["activePageName"] not in pastas:
        erro(f"activePageName {meta['activePageName']} não existe")

    nomes_visuais = Counter()
    nomes_paginas = Counter()
    for pid in pastas:
        pj = paginas_dir / pid / "page.json"
        if not pj.exists():
            erro(f"Página {pid} sem page.json")
            continue
        pagina = ler_json(pj)
        exib = pagina.get("displayName", pid)
        nomes_paginas[exib] += 1
        if pagina.get("name") != pid:
            erro(f"page.json de {pid} tem name='{pagina.get('name')}' (deve ser igual à pasta)")
        W, H = pagina.get("width", 1280), pagina.get("height", 720)
        retangulos = []
        zs = Counter()
        for vj in sorted((paginas_dir / pid).glob("visuals/*/visual.json")):
            vid = vj.parent.name
            v = ler_json(vj)
            nomes_visuais[vid] += 1
            if v.get("name") != vid:
                erro(f"[{exib}] visual {vid} tem name='{v.get('name')}' (deve ser igual à pasta)")
            if not v.get("$schema"):
                aviso(f"[{exib}] visual {vid} sem $schema")
            pos = v.get("position", {})
            x, y, w, h = (pos.get(k, 0) for k in ("x", "y", "width", "height"))
            if x < 0 or y < 0 or x + w > W + 1 or y + h > H + 1:
                aviso(f"[{exib}] visual {vid} sai dos limites da página {W}x{H}")
            zs[pos.get("z")] += 1
            retangulos.append((vid, x, y, w, h, v.get("visual", {}).get("visualType")))
            if "visualGroup" in v:
                continue
            for campo in iterar_campos(v):
                tipo, ent, prop = campo
                if not tabelas:
                    break
                if ent not in tabelas:
                    erro(f"[{exib}] visual {vid}: tabela '{ent}' não existe no modelo")
                elif tipo == "Measure" and prop not in tabelas[ent]["medidas"]:
                    dica = " (existe como coluna)" if prop in tabelas[ent]["colunas"] else ""
                    erro(f"[{exib}] visual {vid}: medida {ent}[{prop}] não existe{dica}")
                elif tipo == "Column" and prop not in tabelas[ent]["colunas"]:
                    dica = " (existe como medida)" if prop in tabelas[ent]["medidas"] else ""
                    erro(f"[{exib}] visual {vid}: coluna {ent}[{prop}] não existe{dica}")
        for zval, n in zs.items():
            if n > 1 and len(retangulos) > 1:
                aviso(f"[{exib}] {n} visuais com o mesmo z={zval} (ordem de tabulação/sobreposição ambígua)")
        for i in range(len(retangulos)):
            for j in range(i + 1, len(retangulos)):
                a, b = retangulos[i], retangulos[j]
                ox = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
                oy = min(a[2] + a[4], b[2] + b[4]) - max(a[2], b[2])
                if ox > 4 and oy > 4 and "shape" not in (a[5], b[5]) and "image" not in (a[5], b[5]):
                    aviso(f"[{exib}] visuais {a[0]} ({a[5]}) e {b[0]} ({b[5]}) se sobrepõem")
    for nome, n in nomes_visuais.items():
        if n > 1:
            aviso(f"ID de visual {nome} usado em {n} páginas (aceito pelo Desktop, mas evite em visuais novos)")
    for nome, n in nomes_paginas.items():
        if n > 1:
            aviso(f"{n} páginas com o mesmo nome de exibição '{nome}'")
    return problemas


def iterar_campos(no):
    """Percorre o JSON e devolve (Column|Measure, Entidade, Propriedade) de cada referência simples."""
    if isinstance(no, dict):
        for tipo in ("Column", "Measure"):
            alvo = no.get(tipo)
            if isinstance(alvo, dict) and "Property" in alvo:
                ent = alvo.get("Expression", {}).get("SourceRef", {}).get("Entity")
                if ent:
                    yield tipo, ent, alvo["Property"]
        for valor in no.values():
            yield from iterar_campos(valor)
    elif isinstance(no, list):
        for item in no:
            yield from iterar_campos(item)


def imprimir_problemas(problemas):
    erros = [m for n, m in problemas if n == "ERRO"]
    avisos = [m for n, m in problemas if n == "AVISO"]
    for m in erros:
        print(f"ERRO  {m}")
    for m in avisos:
        print(f"AVISO {m}")
    print(f"\nValidação: {len(erros)} erro(s), {len(avisos)} aviso(s)")


def cmd_validar(args):
    report, modelo = localizar(args.projeto)
    print(f"Relatório: {report}\nModelo:    {modelo}")
    problemas = validar(report, modelo)
    imprimir_problemas(problemas)
    if any(n == "ERRO" for n, _ in problemas):
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("campos")
    a.add_argument("projeto")
    a.add_argument("--busca")
    a.add_argument("--tabela")
    a.set_defaults(func=cmd_campos)
    a = sub.add_parser("criar")
    a.add_argument("projeto")
    a.add_argument("spec")
    a.add_argument("--simular", action="store_true")
    a.set_defaults(func=cmd_criar)
    a = sub.add_parser("validar")
    a.add_argument("projeto")
    a.set_defaults(func=cmd_validar)
    args = ap.parse_args()
    try:
        args.func(args)
    except Erro as e:
        print(f"ERRO  {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
