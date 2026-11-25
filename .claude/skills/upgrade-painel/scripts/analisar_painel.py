#!/usr/bin/env python3
"""Analisa um painel Power BI e propõe melhorias e novas visões.

Uso:
  analisar_painel.py analisar <entrada> [--saida PASTA]
  analisar_painel.py comparar <entrada_antes> <entrada_depois>

<entrada>: pasta PBIP, arquivo .pbip, pasta *.Report, .zip com PBIP/PBIX/PBIT, .pbit ou .pbix.
  - PBIP e PBIT: relatório + modelo semântico completos.
  - PBIX: relatório completo; o modelo é binário, então os campos são inferidos dos visuais.

Saídas em --saida (padrão ./analise_<nome>): inventario.json, analise.json, relatorio.md e
specs/NV-xx.json (especificações prontas para pbir-paginas-visuais/scripts/pbir_tool.py criar).
"""
import argparse
import json
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

# ============================================================================ util
def ler_json_texto(b: bytes):
    for enc in ("utf-8-sig", "utf-16", "utf-16-le"):
        try:
            return json.loads(b.decode(enc))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError("JSON ilegível")


def ler_json(p: Path):
    return ler_json_texto(p.read_bytes())


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()


def literal(v):
    """Extrai valor de {"expr":{"Literal":{"Value":"'x'"}}} ou {"solid":{"color":...}}."""
    if not isinstance(v, dict):
        return v
    if "solid" in v:
        return literal(v["solid"].get("color"))
    val = v.get("expr", {}).get("Literal", {}).get("Value")
    if val is None:
        return None
    if isinstance(val, str):
        if len(val) >= 2 and val[0] == "'" and val[-1] == "'":
            return val[1:-1].replace("''", "'")
        if re.fullmatch(r"-?\d+(\.\d+)?[DLM]?", val):
            return float(val.rstrip("DLM"))
        if val in ("true", "false"):
            return val == "true"
    return val


def prop(objs, grupo, chave):
    try:
        return literal(objs[grupo][0]["properties"][chave])
    except (KeyError, IndexError, TypeError):
        return None


RE_HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")


def luminancia(hexa):
    hexa = hexa.lstrip("#")
    c = [int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(a, b):
    la, lb = sorted([luminancia(a), luminancia(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def saturada(hexa):
    h = hexa.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return max(r, g, b) - min(r, g, b) > 40


def matiz(hexa):
    h = hexa.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == mn:
        return None
    d = mx - mn
    if mx == r:
        hue = (60 * ((g - b) / d) + 360) % 360
    elif mx == g:
        hue = 60 * ((b - r) / d) + 120
    else:
        hue = 60 * ((r - g) / d) + 240
    return hue


def pt(valor):
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    m = re.match(r"^'?(\d+(?:\.\d+)?)\s*(pt|px|D)?'?$", str(valor).strip())
    if not m:
        return None
    n = float(m.group(1))
    return n * 0.75 if m.group(2) == "px" else n


# ============================================================================ classificações
TIPOS_DECORATIVOS = {"textbox", "shape", "basicShape", "image", "actionButton", "pageNavigator",
                     "bookmarkNavigator", "group"}
TIPOS_SEGMENTACAO = {"slicer", "advancedSlicerVisual", "listSlicer", "textSlicer"}
TIPOS_CARTAO = {"card", "cardVisual", "multiRowCard", "kpi"}
TIPOS_TABELA = {"tableEx", "pivotTable", "table", "matrix"}
TIPOS_PIZZA = {"pieChart", "donutChart"}
TIPOS_COMBO = {"lineClusteredColumnComboChart", "lineStackedColumnComboChart"}
TIPOS_EMPILHADO = {"stackedBarChart", "columnChart", "hundredPercentStackedBarChart",
                   "hundredPercentStackedColumnChart", "stackedAreaChart"}
TIPOS_BARRA = {"clusteredBarChart", "clusteredColumnChart", "barChart", "columnChart", "stackedBarChart"}
SUPORTADOS_GERADOR = {"card", "slicer", "tableEx", "pivotTable", "clusteredBarChart", "clusteredColumnChart",
                      "lineChart", "donutChart", "textbox"}

RE_TEMPO = re.compile(r"(^|[^a-z])(data|date|dt|ano|mes|anomes|competencia|periodo|semana|dia|trimestre|"
                      r"semestre|year|month|quarter|week|day)([^a-z]|$)")
RE_ID = re.compile(r"(^id|id$|_id|key$|^cod|^codigo|^sk_|^nk_|guid)", re.I)
RE_META = re.compile(r"\b(meta|target|objetivo|orcado|orcamento|plano|planejad|previst)", re.I)
RE_VARIACAO = re.compile(r"\b(gap|var|variacao|diferenca|desvio|delta|yoy|mom)\b", re.I)
RE_RAZAO = re.compile(r"(%|percent|taxa|atingimento|ratio|indice|participacao|share)", re.I)
RE_QUALIDADE = re.compile(r"(pendenc|sem |invalid|inconsist|erro|duplic|nulo|vazio|faltante|ausente|"
                          r"divergen|nao encontrad)", re.I)
RE_PAGINA_OPERACIONAL = re.compile(r"(export|conferenc|comparar|de-para|depara|lista|extrac|carga|"
                                   r"localizar|catalogo|detalh|validac|diagnost)", re.I)
RE_TITULO_GENERICO = re.compile(r"^(soma|contagem|media|count|sum|average|total|min|max|first|last)\s+(de|of)\b",
                                re.I)
RE_PAGINA_GENERICA = re.compile(r"^(pagina|page|página)\s*\d+$|^analise exploratoria$|^duplicata", re.I)
STOP = {"de", "da", "do", "das", "dos", "no", "na", "nos", "nas", "em", "por", "e", "a", "o", "as", "os",
        "com", "sem", "para", "total", "qtd", "quantidade", "meta", "gap", "var", "previsto", "prevista",
        "realizado", "realizada", "atingimento", "%", "-", "no painel", "exibicao", "parcial"}


def tokens(nome):
    return {t for t in re.split(r"[\s_\-()\[\]]+", sem_acento(nome)) if t and t not in STOP}


def classe_medida(nome):
    n = sem_acento(nome)
    if RE_QUALIDADE.search(n):
        return "qualidade"
    if RE_VARIACAO.search(n):
        return "variacao"
    if re.search(r"\bmeta\b|target|objetivo|orcad", n):
        return "meta"
    if RE_RAZAO.search(n):
        return "razao"
    return "base"


def eh_tempo(nome, tipo=None):
    nome = re.sub(r"([a-z\u00e0-\u00ff])([A-Z])", r"\1 \2", nome or "")
    return (tipo or "").lower() in ("datetime", "date") or bool(RE_TEMPO.search(sem_acento(nome)))


def granularidade(nome):
    n = sem_acento(re.sub(r"([a-z])([A-Z])", r"\1 \2", nome))
    if re.search(r"ano ?mes|competencia|\bmes\b|month", n):
        return 0
    if re.search(r"\bdata\b|\bdate\b|\bdia\b|\bday\b|semana|week", n):
        return 1
    if re.search(r"trimestre|quarter|semestre", n):
        return 2
    return 3


# ============================================================================ modelo: TMDL
RE_NOME_OBJ = re.compile(r"^(?:'((?:[^']|'')+)'|([^\s=]+))\s*(?:=\s*(.*))?$")
RE_COLREF = re.compile(r"^(?:'((?:[^']|'')+)'|([^.]+))\.(?:'((?:[^']|'')+)'|(.+))$")


def _nome_obj(texto):
    m = RE_NOME_OBJ.match(texto.strip())
    if not m:
        return texto.strip(), None
    return (m.group(1) or m.group(2)).replace("''", "'"), m.group(3)


def _indent(raw):
    lead = raw[: len(raw) - len(raw.lstrip())]
    return lead.count("\t") + lead.count(" ") // 4


def ler_tmdl(pasta_modelo: Path):
    modelo = {"lido": True, "fonte": "TMDL", "tabelas": {}, "relacoes": []}
    arquivos = sorted((pasta_modelo / "definition").rglob("*.tmdl"))
    if not arquivos:
        bim = pasta_modelo / "model.bim"
        if bim.exists():
            return ler_bim(ler_json(bim))
        return {"lido": False, "fonte": None, "tabelas": {}, "relacoes": []}
    for arq in arquivos:
        tabela = rel = obj = None
        desc, cerca, em_expr = [], False, False
        for raw in arq.read_text(encoding="utf-8-sig").splitlines():
            s = raw.strip()
            if cerca:
                if s.startswith("```"):
                    cerca = False
                elif obj is not None:
                    obj["expressao"] += "\n" + s
                continue
            if not s:
                continue
            ind = _indent(raw)
            if s.startswith("///"):
                desc.append(s[3:].strip())
                continue
            if ind == 0:
                obj, em_expr = None, False
                if s.startswith("table "):
                    nome, _ = _nome_obj(s[6:])
                    tabela = modelo["tabelas"].setdefault(nome, {"colunas": {}, "medidas": {}, "data": False,
                                                                 "oculta": False, "descricao": " ".join(desc)})
                    rel = None
                elif s.startswith("relationship "):
                    rel = {"id": s[13:].strip()}
                    modelo["relacoes"].append(rel)
                    tabela = None
                else:
                    tabela = rel = None
                desc = []
                continue
            if ind == 1:
                em_expr = False
                if rel is not None:
                    k, _, v = s.partition(":")
                    rel[k.strip()] = v.strip() if v else True
                    continue
                if tabela is None:
                    continue
                m = re.match(r"^(measure|column|hierarchy|partition|annotation|calculationItem)\s+(.*)$", s)
                if m and m.group(1) in ("measure", "column"):
                    nome, expr = _nome_obj(m.group(2))
                    if m.group(1) == "measure":
                        obj = {"expressao": "", "formato": None, "pasta": None, "descricao": " ".join(desc),
                               "oculta": False}
                        tabela["medidas"][nome] = obj
                        if expr is not None:
                            if expr.strip().startswith("```"):
                                cerca = True
                            else:
                                obj["expressao"] = expr.strip()
                            em_expr = True
                    else:
                        obj = {"tipo": None, "oculta": False, "calculada": expr is not None,
                               "descricao": " ".join(desc), "categoria": None, "formato": None}
                        tabela["colunas"][nome] = obj
                elif m:
                    obj = None
                else:
                    obj = None
                    k, _, v = s.partition(":")
                    if k.strip() == "dataCategory" and v.strip().lower() == "time":
                        tabela["data"] = True
                    if k.strip() == "isHidden":
                        tabela["oculta"] = True
                desc = []
                continue
            # ind >= 2
            if obj is None:
                continue
            mprop = re.match(r"^(\w+)\s*(?::\s*(.*))?$", s) if ind == 2 else None
            if mprop and not (em_expr and ind > 2):
                em_expr = False
                k, v = mprop.group(1), (mprop.group(2) or "").strip()
                if k == "formatString":
                    obj["formato"] = v
                elif k == "displayFolder":
                    obj["pasta"] = v
                elif k == "isHidden":
                    obj["oculta"] = True
                elif k == "dataType":
                    obj["tipo"] = v
                elif k == "dataCategory":
                    obj["categoria"] = v
                elif k == "description":
                    obj["descricao"] = v
            elif em_expr:
                obj["expressao"] += "\n" + s
    for r in modelo["relacoes"]:
        for lado in ("fromColumn", "toColumn"):
            m = RE_COLREF.match(str(r.get(lado, "")))
            if m:
                r[lado] = [(m.group(1) or m.group(2)).replace("''", "'"), (m.group(3) or m.group(4)).replace("''", "'")]
    return modelo


def ler_bim(dados):
    """model.bim (PBIP antigo) ou DataModelSchema (PBIT)."""
    modelo = {"lido": True, "fonte": "BIM", "tabelas": {}, "relacoes": []}
    m = dados.get("model", dados)
    for t in m.get("tables", []):
        tab = modelo["tabelas"][t["name"]] = {"colunas": {}, "medidas": {}, "data": t.get("dataCategory") == "Time",
                                             "oculta": t.get("isHidden", False),
                                             "descricao": _txt(t.get("description"))}
        for c in t.get("columns", []):
            if c.get("type") == "rowNumber":
                continue
            tab["colunas"][c["name"]] = {"tipo": c.get("dataType"), "oculta": c.get("isHidden", False),
                                         "calculada": c.get("type") == "calculated",
                                         "descricao": _txt(c.get("description")),
                                         "categoria": c.get("dataCategory"), "formato": c.get("formatString")}
        for me in t.get("measures", []):
            tab["medidas"][me["name"]] = {"expressao": _txt(me.get("expression")), "formato": me.get("formatString"),
                                          "pasta": me.get("displayFolder"), "descricao": _txt(me.get("description")),
                                          "oculta": me.get("isHidden", False)}
    for r in m.get("relationships", []):
        modelo["relacoes"].append({"fromColumn": [r.get("fromTable"), r.get("fromColumn")],
                                   "toColumn": [r.get("toTable"), r.get("toColumn")],
                                   "isActive": r.get("isActive", True),
                                   "crossFilteringBehavior": r.get("crossFilteringBehavior", "oneDirection")})
    return modelo


def _txt(v):
    return "\n".join(v) if isinstance(v, list) else (v or "")


# ============================================================================ relatório: PBIR
def ref_campo(field, aliases=None):
    """Devolve (Column|Measure, tabela, campo, agregado) da primeira referência dentro de field."""
    agregado = [False]

    def walk(n):
        if isinstance(n, dict):
            if "Aggregation" in n:
                agregado[0] = True
            for chave, tipo in (("Measure", "Measure"), ("Column", "Column"), ("PropertyVariationSource", "Column")):
                alvo = n.get(chave)
                if isinstance(alvo, dict) and "Property" in alvo:
                    sr = alvo.get("Expression", {}).get("SourceRef", {})
                    ent = sr.get("Entity") or (aliases or {}).get(sr.get("Source"))
                    if ent:
                        return tipo, ent, alvo["Property"]
            if "HierarchyLevel" in n:
                r = walk(n["HierarchyLevel"].get("Expression"))
                if r:
                    return r
            for v in n.values():
                r = walk(v)
                if r:
                    return r
        elif isinstance(n, list):
            for v in n:
                r = walk(v)
                if r:
                    return r
        return None

    r = walk(field)
    return (r + (agregado[0],)) if r else None


def fontes(no, saida):
    if isinstance(no, dict):
        for k, v in no.items():
            if k == "fontSize":
                n = pt(literal(v) if isinstance(v, dict) else v)
                if n:
                    saida.append(n)
            else:
                fontes(v, saida)
    elif isinstance(no, list):
        for v in no:
            fontes(v, saida)
    return saida


def texto_paragrafos(objs):
    textos, cores, tamanhos = [], [], []
    try:
        pars = objs["general"][0]["properties"]["paragraphs"]
    except (KeyError, IndexError, TypeError):
        return "", cores, tamanhos
    for p in pars:
        for run in p.get("textRuns", []):
            textos.append(run.get("value", ""))
            st = run.get("textStyle", {})
            if st.get("color"):
                cores.append(st["color"])
            if st.get("fontSize"):
                tamanhos.append(pt(st["fontSize"]))
    return " ".join(textos).strip(), cores, [t for t in tamanhos if t]


def montar_visual(vid, tipo, pos, objs, vco, campos, bruto, filtros=0, grupo=False):
    titulo = prop(vco, "title", "text")
    mostra = prop(vco, "title", "show")
    texto, cores_txt, tam_txt = texto_paragrafos(objs) if tipo == "textbox" else ("", [], [])
    alt = prop(vco, "general", "altText")
    return {
        "id": vid, "tipo": tipo,
        "x": pos.get("x", 0), "y": pos.get("y", 0), "w": pos.get("width", 0), "h": pos.get("height", 0),
        "z": pos.get("z"), "tab": pos.get("tabOrder"),
        "titulo": titulo if isinstance(titulo, str) else None,
        "titulo_visivel": bool(mostra) if mostra is not None else None,
        "texto": texto,
        "campos": campos,
        "cores": sorted({c.upper() for c in RE_HEX.findall(json.dumps(bruto))}),
        "fontes": sorted(set(fontes(bruto, []) + tam_txt)),
        "cor_titulo": prop(vco, "title", "fontColor"),
        "cor_fundo": prop(vco, "background", "color") if prop(vco, "background", "show") is not False else None,
        "cor_valor": prop(objs, "labels", "color"),
        "cor_texto": cores_txt[0] if cores_txt else None,
        "borda": prop(vco, "border", "show") is True,
        "sombra": prop(vco, "dropShadow", "show") is True,
        "alt_text": bool(alt),
        "filtros": filtros,
        "grupo": grupo,
    }


def ler_pbir(report: Path):
    defin = report / "definition"
    rep = ler_json(defin / "report.json") if (defin / "report.json").exists() else {}
    meta = ler_json(defin / "pages" / "pages.json") if (defin / "pages" / "pages.json").exists() else {}
    tema = rep.get("themeCollection", {})
    paginas = []
    ordem = meta.get("pageOrder") or sorted(d.name for d in (defin / "pages").iterdir() if d.is_dir())
    for pid in ordem:
        pj = defin / "pages" / pid / "page.json"
        if not pj.exists():
            continue
        p = ler_json(pj)
        visuais = []
        for vj in sorted((defin / "pages" / pid).glob("visuals/*/visual.json")):
            v = ler_json(vj)
            if "visualGroup" in v:
                visuais.append(montar_visual(v.get("name"), "group", v.get("position", {}), {}, {}, [], {}, grupo=True))
                continue
            vis = v.get("visual", {})
            campos = []
            for papel, bloco in (vis.get("query", {}).get("queryState", {}) or {}).items():
                for proj in bloco.get("projections", []):
                    r = ref_campo(proj.get("field"))
                    if r:
                        campos.append({"papel": papel, "tipo": r[0], "tabela": r[1], "campo": r[2], "agregado": r[3]})
            nf = len(v.get("filterConfig", {}).get("filters", []))
            visuais.append(montar_visual(v.get("name"), vis.get("visualType", "?"), v.get("position", {}),
                                         vis.get("objects", {}), vis.get("visualContainerObjects", {}),
                                         campos, v, nf))
        paginas.append({
            "id": pid, "nome": p.get("displayName", pid), "largura": p.get("width", 1280),
            "altura": p.get("height", 720), "ajuste": p.get("displayOption"),
            "fundo": prop(p.get("objects", {}), "background", "color"),
            "oculta": p.get("visibility") == "HiddenInViewMode",
            "tipo": (p.get("pageBinding") or {}).get("type") or ("Tooltip" if p.get("type") == "Tooltip" else None),
            "filtros": len(p.get("filterConfig", {}).get("filters", [])),
            "visuais": visuais,
        })
    return {"tema_base": (tema.get("baseTheme") or {}).get("name"),
            "tema_customizado": (tema.get("customTheme") or {}).get("name"),
            "paginas": paginas}


# ============================================================================ relatório: Layout legado (PBIX/PBIT)
def _json_str(s):
    if isinstance(s, str):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return {}
    return s or {}


def ler_layout(layout):
    cfg = _json_str(layout.get("config"))
    tema = cfg.get("themeCollection", {})
    paginas = []
    for sec in sorted(layout.get("sections", []), key=lambda s: s.get("ordinal", 0)):
        scfg = _json_str(sec.get("config"))
        visuais = []
        for vc in sec.get("visualContainers", []):
            c = _json_str(vc.get("config"))
            sv = c.get("singleVisual") or {}
            if not sv and c.get("singleVisualGroup"):
                visuais.append(montar_visual(c.get("name"), "group", vc, {}, {}, [], {}, grupo=True))
                continue
            pq = sv.get("prototypeQuery", {})
            aliases = {f.get("Name"): f.get("Entity") for f in pq.get("From", [])}
            sel = {s.get("Name"): s for s in pq.get("Select", [])}
            campos = []
            for papel, itens in (sv.get("projections") or {}).items():
                for it in itens:
                    s = sel.get(it.get("queryRef"))
                    r = ref_campo(s, aliases) if s else None
                    if r:
                        campos.append({"papel": papel, "tipo": r[0], "tabela": r[1], "campo": r[2], "agregado": r[3]})
            pos = {"x": vc.get("x", 0), "y": vc.get("y", 0), "width": vc.get("width", 0),
                   "height": vc.get("height", 0), "z": vc.get("z"), "tabOrder": vc.get("tabOrder")}
            nf = len(_json_str(vc.get("filters")) or [])
            visuais.append(montar_visual(c.get("name"), sv.get("visualType", "?"), pos, sv.get("objects", {}),
                                         sv.get("vcObjects", {}), campos, c, nf))
        paginas.append({
            "id": sec.get("name"), "nome": sec.get("displayName"), "largura": sec.get("width", 1280),
            "altura": sec.get("height", 720), "ajuste": sec.get("displayOption"),
            "fundo": prop(scfg.get("objects", {}), "background", "color"),
            "oculta": scfg.get("visibility") == 1, "tipo": None,
            "filtros": len(_json_str(sec.get("filters")) or []), "visuais": visuais,
        })
    return {"tema_base": (tema.get("baseTheme") or {}).get("name"),
            "tema_customizado": (tema.get("customTheme") or {}).get("name"), "paginas": paginas}


def modelo_inferido(rel):
    modelo = {"lido": False, "fonte": "inferido dos visuais", "tabelas": {}, "relacoes": []}
    for p in rel["paginas"]:
        for v in p["visuais"]:
            for c in v["campos"]:
                t = modelo["tabelas"].setdefault(c["tabela"], {"colunas": {}, "medidas": {}, "data": False,
                                                               "oculta": False, "descricao": ""})
                if c["tipo"] == "Measure":
                    t["medidas"].setdefault(c["campo"], {"expressao": "", "formato": None, "pasta": None,
                                                         "descricao": "", "oculta": False})
                else:
                    t["colunas"].setdefault(c["campo"], {"tipo": None, "oculta": False, "calculada": False,
                                                         "descricao": "", "categoria": None, "formato": None})
    return modelo


# ============================================================================ ingestão
def extrair_zip(zp: Path, destino: Path):
    with zipfile.ZipFile(zp) as z:
        for info in z.infolist():
            alvo = (destino / info.filename).resolve()
            if not str(alvo).startswith(str(destino.resolve())):
                raise ValueError(f"Caminho suspeito no ZIP: {info.filename}")
        z.extractall(destino)


def carregar_arquivo_pbi(arq: Path):
    """PBIX/PBIT: lê Layout legado ou PBIR embutido e, no PBIT, o DataModelSchema."""
    with zipfile.ZipFile(arq) as z:
        nomes = set(z.namelist())
        if any(n.startswith("Report/definition/pages/") for n in nomes):
            tmp = Path(tempfile.mkdtemp(prefix="pbir_"))
            for n in nomes:
                if n.startswith("Report/definition/"):
                    z.extract(n, tmp)
            rel = ler_pbir(tmp / "Report")
            formato = arq.suffix[1:].upper() + " (PBIR)"
        elif "Report/Layout" in nomes:
            rel = ler_layout(ler_json_texto(z.read("Report/Layout")))
            formato = arq.suffix[1:].upper()
        else:
            raise ValueError(f"{arq.name}: não encontrei Report/Layout nem Report/definition")
        if "DataModelSchema" in nomes:
            modelo = ler_bim(ler_json_texto(z.read("DataModelSchema")))
        else:
            modelo = modelo_inferido(rel)
    return formato, rel, modelo


def carregar_report_pasta(report: Path):
    if (report / "definition" / "pages").exists():
        rel, formato = ler_pbir(report), "PBIP (PBIR)"
    elif (report / "report.json").exists():
        rel, formato = ler_layout(ler_json(report / "report.json")), "PBIP (report.json legado)"
    else:
        raise ValueError(f"{report}: formato de relatório não reconhecido")
    modelo_dir = None
    pbir = report / "definition.pbir"
    if pbir.exists():
        caminho = ler_json(pbir).get("datasetReference", {}).get("byPath", {}).get("path")
        if caminho and (report / caminho).exists():
            modelo_dir = (report / caminho).resolve()
    if modelo_dir is None:
        alt = report.parent / (report.name[: -len(".Report")] + ".SemanticModel")
        modelo_dir = alt if alt.exists() else None
    modelo = ler_tmdl(modelo_dir) if modelo_dir else modelo_inferido(rel)
    if not modelo["lido"]:
        modelo = modelo_inferido(rel)
    return formato, rel, modelo


def carregar(entrada: str):
    """Devolve lista de (nome, formato, relatorio, modelo)."""
    p = Path(entrada).resolve()
    if p.is_file() and p.suffix.lower() == ".pbip":
        p = p.parent
    if p.is_file() and p.suffix.lower() == ".zip":
        tmp = Path(tempfile.mkdtemp(prefix="painel_"))
        extrair_zip(p, tmp)
        itens = carregar_pasta(tmp)
        for z in tmp.rglob("*.zip"):  # ZIP dentro de ZIP (um nível)
            sub = z.with_suffix("")
            extrair_zip(z, sub)
            itens += carregar_pasta(sub)
        if not itens:
            raise ValueError(f"{p.name}: nenhum relatório Power BI encontrado no ZIP")
        return itens
    if p.is_file() and p.suffix.lower() in (".pbix", ".pbit"):
        formato, rel, modelo = carregar_arquivo_pbi(p)
        return [(p.stem, formato, rel, modelo)]
    if p.is_dir():
        itens = carregar_pasta(p)
        if not itens:
            raise ValueError(f"{p}: nenhum relatório Power BI encontrado")
        return itens
    raise ValueError(f"Entrada não reconhecida: {entrada}")


def carregar_pasta(p: Path):
    itens = []
    reports = [p] if p.name.endswith(".Report") else sorted(p.rglob("*.Report"))
    for r in reports:
        if r.is_dir():
            formato, rel, modelo = carregar_report_pasta(r)
            itens.append((r.name[: -len(".Report")], formato, rel, modelo))
    for f in sorted(list(p.rglob("*.pbix")) + list(p.rglob("*.pbit"))):
        formato, rel, modelo = carregar_arquivo_pbi(f)
        itens.append((f.stem, formato, rel, modelo))
    return itens


# ============================================================================ uso de campos
def usos(rel):
    cont = Counter()
    por_visual = []
    for p in rel["paginas"]:
        for v in p["visuais"]:
            for c in v["campos"]:
                cont[(c["tabela"], c["campo"])] += 1
            por_visual.append((p, v))
    return cont, por_visual


def medidas_referenciadas(modelo):
    refs = set()
    todas = {m for t in modelo["tabelas"].values() for m in t["medidas"]}
    for t in modelo["tabelas"].values():
        for m in t["medidas"].values():
            for nome in re.findall(r"\[([^\]]+)\]", m.get("expressao") or ""):
                if nome in todas:
                    refs.add(nome)
    return refs


def tabelas_dimensao(modelo):
    dims = set()
    for r in modelo["relacoes"]:
        to = r.get("toColumn")
        if isinstance(to, list):
            dims.add(to[0])
    for nome, t in modelo["tabelas"].items():
        if sem_acento(nome).startswith(("dim", "d_", "calend")):
            dims.add(nome)
        elif not t["medidas"] and t["colunas"] and not sem_acento(nome).startswith(("fato", "fact", "f_")):
            dims.add(nome)
    return dims


# ============================================================================ auditoria
PESO = {"alta": 15, "média": 7, "baixa": 3}
CATEGORIAS = ["Contexto e narrativa", "Escolha do visual", "Desordem e layout", "Foco e cor",
              "Acessibilidade", "Navegação", "Modelo e desempenho"]


class Auditoria:
    def __init__(self):
        self.achados = []

    def add(self, codigo, categoria, severidade, principio, titulo, evidencia, recomendacao, esforco="baixo",
            automatizavel=False, pagina=None, visuais=None):
        self.achados.append({"codigo": codigo, "categoria": categoria, "severidade": severidade,
                             "principio": principio, "titulo": titulo, "pagina": pagina,
                             "visuais": visuais or [], "evidencia": evidencia, "recomendacao": recomendacao,
                             "esforco": esforco, "automatizavel": automatizavel})


def eh_operacional(p):
    dados = [v for v in p["visuais"] if v["tipo"] not in TIPOS_DECORATIVOS | TIPOS_SEGMENTACAO]
    tabelas = [v for v in dados if v["tipo"] in TIPOS_TABELA]
    return bool(dados) and (len(tabelas) / len(dados) >= 0.8 or bool(RE_PAGINA_OPERACIONAL.search(sem_acento(p["nome"]))))


def proximos_nao_iguais(valores, tol=8):
    vs = sorted(set(round(v) for v in valores))
    return sum(1 for a, b in zip(vs, vs[1:]) if 0 < b - a <= tol)


def auditar(rel, modelo):
    a = Auditoria()
    paginas = rel["paginas"]
    cont, _ = usos(rel)
    tempo_cols = {(t, c) for t, tab in modelo["tabelas"].items() for c, col in tab["colunas"].items()
                  if eh_tempo(c, col.get("tipo"))}
    todas_medidas = {m: t for t, tab in modelo["tabelas"].items() for m in tab["medidas"]}

    visiveis = [p for p in paginas if not p["oculta"] and p["tipo"] not in ("Tooltip", "Drillthrough")]
    # ---------------------------------------------------------------- nível relatório
    tem_resumo = any(sum(1 for v in p["visuais"] if v["tipo"] in TIPOS_CARTAO and v["y"] < 0.35 * p["altura"]) >= 2
                     for p in paginas)
    if visiveis and not tem_resumo:
        a.add("H04", "Contexto e narrativa", "alta", "L1 Contexto · L6 História · [Pirâmide]",
              "Não há página de resumo explicativa",
              "Nenhuma página tem dois ou mais KPIs no topo; o público começa por tabelas/gráficos de detalhe.",
              "Criar uma página inicial com manchete (grande ideia), 3–4 KPIs com comparação e 1–2 visuais de "
              "tendência/ranking. Ver novas visões (Resumo executivo).", "médio", True)
    if visiveis and eh_operacional(visiveis[0]) and len(visiveis) > 1:
        a.add("H05", "Contexto e narrativa", "média", "L1 Exploratório × explicativo",
              "A primeira página é operacional/de conferência",
              f"'{visiveis[0]['nome']}' é composta por tabelas de detalhe.",
              "Mover páginas de conferência/exportação para o fim (ou ocultá-las) e abrir com a visão gerencial.",
              "baixo", True)
    if not rel.get("tema_customizado"):
        a.add("C02", "Foco e cor", "baixa", "L4 Cor consistente · [Nielsen 4]",
              "Relatório sem tema corporativo",
              f"Só o tema base '{rel.get('tema_base')}' está aplicado; cores e bordas são formatadas visual a visual.",
              "Criar um tema JSON (paleta: base cinza + cor de destaque + cores de status, Segoe UI, bordas e "
              "sombras desligadas) e aplicá-lo ao relatório.", "médio")
    tamanhos = Counter((p["largura"], p["altura"]) for p in visiveis)
    if len(tamanhos) > 1 and not all(eh_operacional(p) for p in visiveis):
        a.add("D08", "Desordem e layout", "baixa", "[Nielsen 4] Consistência",
              "Tamanhos de página diferentes",
              ", ".join(f"{w}×{h} ({n} pág.)" for (w, h), n in tamanhos.most_common()),
              "Padronizar o tamanho das páginas gerenciais (as de conferência podem manter o próprio).", "baixo")
    navegacao = any(v["tipo"] in ("actionButton", "pageNavigator", "bookmarkNavigator")
                    for p in paginas for v in p["visuais"])
    if len(visiveis) > 7 and not navegacao:
        a.add("N01", "Navegação", "média", "[Shneiderman] · [Nielsen 7]",
              f"{len(visiveis)} páginas visíveis sem navegação",
              "Não há navegador de páginas nem botões de ação.",
              "Agrupar as páginas por tema, incluir navegador de páginas e ocultar as de detalhe (drill-through).",
              "médio")
    sem_alt = sum(1 for p in paginas for v in p["visuais"]
                  if v["tipo"] not in TIPOS_DECORATIVOS and not v["alt_text"])
    if sem_alt:
        a.add("A03", "Acessibilidade", "baixa", "[WCAG] · [Microsoft]",
              "Visuais sem texto alternativo",
              f"{sem_alt} visual(is) de dados sem texto alternativo.",
              "Preencher o texto alternativo (Geral › Texto alternativo) com o que o visual mostra e a conclusão.",
              "baixo", True)
    genericas = [p["nome"] for p in paginas if RE_PAGINA_GENERICA.search(sem_acento(p["nome"] or ""))]
    if genericas:
        a.add("H03", "Contexto e narrativa", "baixa", "L6 Lógica horizontal",
              "Nomes de página genéricos", ", ".join(genericas),
              "Renomear com o tema ou a pergunta que a página responde.", "baixo", True)
    nomes_rep = [n for n, k in Counter(p["nome"] for p in paginas).items() if k > 1]
    if nomes_rep:
        a.add("H06", "Navegação", "baixa", "[Nielsen 4]", "Páginas com o mesmo nome", ", ".join(nomes_rep),
              "Dar nomes distintos às páginas.", "baixo", True)

    # ---------------------------------------------------------------- nível página
    for p in paginas:
        nome = p["nome"]
        oper = eh_operacional(p)
        vs = [v for v in p["visuais"] if v["tipo"] != "group"]
        dados = [v for v in vs if v["tipo"] not in TIPOS_DECORATIVOS | TIPOS_SEGMENTACAO]
        segs = [v for v in vs if v["tipo"] in TIPOS_SEGMENTACAO]
        W, H = p["largura"], p["altura"]
        fundo_pag = p["fundo"] if isinstance(p["fundo"], str) else "#FFFFFF"

        if p["tipo"] in ("Tooltip",):
            continue
        cabecalho = [v for v in vs if v["tipo"] in ("textbox", "image", "shape", "basicShape") and v["y"] < 0.12 * H]
        if dados and not cabecalho and not oper:
            a.add("H01", "Contexto e narrativa", "média", "L5 Texto explica · L6 Títulos de ação",
                  "Página sem manchete", f"'{nome}' não tem título/manchete no topo.",
                  "Adicionar caixa de texto no topo com a conclusão da página (título de ação) e o período.",
                  "baixo", True, nome)
        sem_titulo = [v for v in dados if v["tipo"] not in TIPOS_CARTAO
                      and (v["titulo_visivel"] is False or (v["titulo_visivel"] and not v["titulo"]))]
        genericos = [v for v in dados if v["titulo"] and RE_TITULO_GENERICO.search(sem_acento(v["titulo"]))]
        if sem_titulo:
            a.add("H02", "Contexto e narrativa", "média" if not oper else "baixa", "L6 Títulos de ação",
                  "Visuais sem título", f"{len(sem_titulo)} visual(is) em '{nome}' sem título visível.",
                  "Dar a cada visual um título que diga a conclusão (ex.: 'Niterói concentra 40% das pendências').",
                  "baixo", True, nome, [v["id"] for v in sem_titulo])
        if genericos:
            a.add("H02", "Contexto e narrativa", "baixa", "L6 Títulos de ação",
                  "Títulos automáticos", "; ".join(v["titulo"] for v in genericos[:5]),
                  "Trocar 'Soma de X por Y' por um título de ação ou, no mínimo, um nome de negócio.",
                  "baixo", True, nome, [v["id"] for v in genericos])

        # densidade
        if len(dados) > 10 and not oper:
            a.add("D01", "Desordem e layout", "alta", "L3 Carga cognitiva · [Few]",
                  "Visuais demais na página", f"'{nome}' tem {len(dados)} visuais de dados.",
                  "Manter até 8–10: priorizar os que sustentam a manchete, mover o restante para uma página de "
                  "detalhe, tooltip ou bookmark. Também reduz o tempo de carga.", "médio", False, nome)
        elif len(dados) > 8 and not oper:
            a.add("D01", "Desordem e layout", "média", "L3 Carga cognitiva · [Few]",
                  "Página densa", f"'{nome}' tem {len(dados)} visuais de dados.",
                  "Revisar se todos sustentam a mensagem da página.", "médio", False, nome)
        if len(segs) > 4:
            a.add("D02", "Desordem e layout", "média", "L3 · [Nielsen 8]",
                  "Segmentações demais", f"'{nome}' tem {len(segs)} segmentações.",
                  "Deixar 2–4 visíveis (período, unidade) e levar as demais ao painel de filtros ou a um painel "
                  "lateral recolhível (bookmark). Sincronizar segmentações entre páginas.", "médio", False, nome)

        # limites, sobreposição, alinhamento
        fora = [v for v in vs if v["x"] < 0 or v["y"] < 0 or v["x"] + v["w"] > W + 1 or v["y"] + v["h"] > H + 1]
        if fora:
            a.add("D05", "Desordem e layout", "alta", "L3 Ordem visual",
                  "Visuais fora da página", f"{len(fora)} visual(is) passam do limite {W}×{H} em '{nome}'.",
                  "Reposicionar dentro da página.", "baixo", True, nome, [v["id"] for v in fora])
        sobre = []
        solidos = [v for v in vs if v["tipo"] not in ("shape", "basicShape", "image")]
        for i in range(len(solidos)):
            for j in range(i + 1, len(solidos)):
                v1, v2 = solidos[i], solidos[j]
                ox = min(v1["x"] + v1["w"], v2["x"] + v2["w"]) - max(v1["x"], v2["x"])
                oy = min(v1["y"] + v1["h"], v2["y"] + v2["h"]) - max(v1["y"], v2["y"])
                if ox > 4 and oy > 4:
                    sobre.append((v1["id"], v2["id"]))
        if sobre:
            a.add("D04", "Desordem e layout", "média", "L3 Ordem visual",
                  "Visuais sobrepostos", f"{len(sobre)} par(es) sobrepostos em '{nome}'.",
                  "Separar os visuais respeitando a grade; usar fundo/forma apenas como agrupador.",
                  "baixo", True, nome, sorted({i for par in sobre for i in par}))
        desal = (proximos_nao_iguais([v["x"] for v in vs]) + proximos_nao_iguais([v["y"] for v in vs])
                 + proximos_nao_iguais([v["x"] + v["w"] for v in vs]))
        if desal >= 2:
            a.add("D03", "Desordem e layout", "baixa", "L3 Ordem visual · Gestalt",
                  "Pequenos desalinhamentos", f"{desal} bordas quase alinhadas (diferença de 1–8 px) em '{nome}'.",
                  "Alinhar à grade (margem 24, espaçamento 16–24).", "baixo", True, nome)
        decor = [v for v in dados if v["borda"] or v["sombra"]]
        if len(decor) >= 3:
            a.add("D07", "Desordem e layout", "baixa", "L3 Eliminar desordem",
                  "Bordas/sombras em excesso", f"{len(decor)} visuais com borda ou sombra em '{nome}'.",
                  "Desligar bordas e sombras; agrupar por espaço em branco ou um fundo único.",
                  "baixo", True, nome)
        zs = Counter(v["z"] for v in vs)
        if len(vs) > 1 and any(n > 1 for n in zs.values()):
            a.add("A04", "Acessibilidade", "baixa", "[Microsoft] Ordem de tabulação",
                  "Ordem de camada/tabulação repetida",
                  f"Em '{nome}', {sum(n for n in zs.values() if n > 1)} visuais compartilham o mesmo z/tabOrder.",
                  "Numerar z e tabOrder seguindo a leitura (esquerda→direita, cima→baixo).", "baixo", True, nome)

        # cor
        cores = {c for v in vs for c in v["cores"]} | ({fundo_pag.upper()} if fundo_pag else set())
        vivas = {c for c in cores if saturada(c)}
        if len(vivas) > 6:
            a.add("C01", "Foco e cor", "média", "L4 Cor com parcimônia",
                  "Cores demais", f"{len(vivas)} cores saturadas em '{nome}': {', '.join(sorted(vivas)[:10])}.",
                  "Usar base cinza + 1 cor de destaque + cores de status; levar a paleta para o tema.",
                  "médio", False, nome)
        hues = [matiz(c) for c in vivas]
        if any(h is not None and (h < 20 or h > 340) for h in hues) and any(h is not None and 90 < h < 160 for h in hues):
            a.add("C03", "Acessibilidade", "baixa", "L4 · [WCAG] Não depender só da cor",
                  "Vermelho e verde na mesma página",
                  f"'{nome}' usa vermelho e verde; ~8% dos homens não distinguem essas cores.",
                  "Usar azul/laranja para bom/ruim ou acrescentar ícone/rótulo ao status.", "baixo", False, nome)

        # contraste e fontes
        baixos = []
        for v in vs:
            fundo_v = v["cor_fundo"] if isinstance(v["cor_fundo"], str) else fundo_pag
            for cor_t in (v["cor_titulo"], v["cor_valor"], v["cor_texto"]):
                if isinstance(cor_t, str) and RE_HEX.fullmatch(cor_t) and RE_HEX.fullmatch(fundo_v or ""):
                    r = contraste(cor_t, fundo_v)
                    if r < 4.5:
                        baixos.append(f"{v['id']} {cor_t} sobre {fundo_v} ({r:.1f}:1)")
        if baixos:
            a.add("A01", "Acessibilidade", "média", "L5 Acessibilidade · [WCAG] 4,5:1",
                  "Contraste de texto insuficiente", "; ".join(baixos[:4]),
                  "Escurecer o texto ou clarear o fundo até pelo menos 4,5:1.", "baixo", True, nome)
        pequenas = sorted({f for v in vs for f in v["fontes"] if f < 9})
        if pequenas:
            a.add("A02", "Acessibilidade", "baixa", "L5 Acessibilidade",
                  "Fontes pequenas", f"Tamanhos {', '.join(str(int(f)) for f in pequenas)} pt em '{nome}'.",
                  "Usar no mínimo 10 pt em rótulos e 12 pt em títulos.", "baixo", True, nome)

        # KPI no topo
        cards = [v for v in dados if v["tipo"] in TIPOS_CARTAO]
        graficos = [v for v in dados if v["tipo"] not in TIPOS_CARTAO]
        if cards and graficos and min(v["y"] for v in cards) > min(v["y"] for v in graficos) + 40:
            a.add("H07", "Contexto e narrativa", "baixa", "[Z/F] · [Pirâmide]",
                  "KPIs abaixo dos gráficos", f"Em '{nome}' os cartões não estão no topo.",
                  "Subir os KPIs para a primeira faixa (leitura em Z), gráficos no meio, detalhe embaixo.",
                  "baixo", True, nome)

        # nível visual
        for v in dados:
            t, campos = v["tipo"], v["campos"]
            cat = [c for c in campos if c["papel"] in ("Category", "Axis", "Rows")]
            ys = [c for c in campos if c["papel"] in ("Y", "Values")]
            series = [c for c in campos if c["papel"] in ("Series", "Legend")]
            tit = v["titulo"] or v["id"]
            if t in TIPOS_PIZZA:
                a.add("G01", "Escolha do visual", "média", "L2 Evite pizza/rosca · [Few]",
                      "Gráfico de pizza/rosca", f"'{tit}' em '{nome}'.",
                      "Trocar por barras horizontais ordenadas (comparar comprimentos é mais preciso que ângulos); "
                      "se for parte-todo com 2 categorias, usar cartão com %.", "baixo", True, nome, [v["id"]])
            elif t == "gauge":
                a.add("G02", "Escolha do visual", "baixa", "L2 · [Few]",
                      "Medidor (gauge)", f"'{tit}' em '{nome}'.",
                      "Trocar por cartão com valor, meta e variação, ou barra com marcador de meta (bullet).",
                      "baixo", True, nome, [v["id"]])
            elif t in TIPOS_COMBO:
                a.add("G07", "Escolha do visual", "baixa", "L2 Eixo secundário confunde",
                      "Gráfico com dois eixos", f"'{tit}' em '{nome}'.",
                      "Dividir em dois gráficos alinhados ou mostrar a variação diretamente.", "médio", False,
                      nome, [v["id"]])
            if t == "lineChart" and cat and not any(eh_tempo(c["campo"],
                                                            modelo["tabelas"].get(c["tabela"], {}).get("colunas", {})
                                                            .get(c["campo"], {}).get("tipo")) for c in cat):
                a.add("G03", "Escolha do visual", "média", "L2 Linha só para dados contínuos",
                      "Linha com categoria não temporal", f"'{tit}' usa {cat[0]['tabela']}[{cat[0]['campo']}].",
                      "Usar barras ordenadas para comparar categorias; linha conecta pontos que têm ordem.",
                      "baixo", True, nome, [v["id"]])
            if t in TIPOS_BARRA and cat and all(eh_tempo(c["campo"]) for c in cat):
                a.add("G04", "Escolha do visual", "baixa", "L2 Tempo → linha",
                      "Tempo em barras", f"'{tit}' mostra {cat[0]['campo']} em barras.",
                      "Para muitos períodos ou foco na tendência, usar linha; manter colunas só para poucos períodos.",
                      "baixo", True, nome, [v["id"]])
            if t in TIPOS_TABELA:
                ncol = len(campos)
                if ncol > 10:
                    a.add("G05", "Escolha do visual", "baixa" if oper else "média", "L2 Tabelas para consulta · L3",
                          "Tabela larga", f"'{tit}' em '{nome}' tem {ncol} colunas"
                          + (" (página operacional, densidade esperada)" if oper else "") + ".",
                          "Manter as colunas essenciais, aplicar destaque condicional só ao que exige ação e levar o "
                          "restante para drill-through/tooltip.", "médio", False, nome, [v["id"]])
            if t == "lineChart" and (len(ys) > 4 or series):
                a.add("G06", "Escolha do visual", "baixa", "L4 Foco · evitar espaguete",
                      "Muitas séries na linha", f"'{tit}' tem {len(ys)} medida(s){' e legenda' if series else ''}.",
                      "Destacar a série principal e acinzentar as demais, ou usar múltiplos pequenos.",
                      "médio", False, nome, [v["id"]])
            if t in TIPOS_EMPILHADO and series:
                a.add("G08", "Escolha do visual", "baixa", "L2 Empilhados com cautela",
                      "Barras empilhadas com legenda", f"'{tit}' em '{nome}'.",
                      "Só a primeira série tem base comum; considerar barras agrupadas ou 100% com poucas séries.",
                      "baixo", False, nome, [v["id"]])
            implicitas = [c for c in ys if c["tipo"] == "Column" and c["agregado"]]
            if implicitas and t not in TIPOS_TABELA:
                a.add("G10", "Modelo e desempenho", "baixa", "Boas práticas DAX",
                      "Agregação implícita", f"'{tit}' agrega {', '.join(c['campo'] for c in implicitas)} direto da coluna.",
                      "Criar medidas explícitas (formato, nome de negócio, reuso).", "baixo", False, nome, [v["id"]])
            if t in TIPOS_CARTAO and ys and ys[0]["tipo"] == "Measure":
                med = ys[0]["campo"]
                fmt = (modelo["tabelas"].get(ys[0]["tabela"], {}).get("medidas", {}).get(med, {}) or {}).get("formato")
                texto_ou_data = re.search(r"status|situac|atualiz|data|texto|titulo|rotulo|label|nome",
                                          sem_acento(med)) or (fmt and re.search(r"[dmy]{2,}|hh", fmt, re.I))
                if classe_medida(med) == "base" and not texto_ou_data:
                    tk = tokens(med)
                    relacionadas = [m for m in todas_medidas if m != med and tk & tokens(m)
                                    and classe_medida(m) in ("meta", "variacao", "razao")]
                    na_pagina = {c["campo"] for x in dados for c in x["campos"]}
                    if any(tk & tokens(m) and classe_medida(m) in ("meta", "variacao") for m in na_pagina):
                        continue  # a comparação já está na página
                    a.add("G09", "Escolha do visual", "média" if relacionadas else "baixa",
                          "L1 Contexto · L2 Número com comparação · [Few]",
                          "Cartão sem comparação" + (" (há meta/variação no modelo)" if relacionadas else ""),
                          f"'{v['titulo'] or med}' mostra {med} sem referência."
                          + (f" Medidas candidatas: {', '.join(relacionadas[:3])}." if relacionadas else ""),
                          "Mostrar meta, variação ou período anterior junto do valor (cartão novo com valor de "
                          "referência, ou subtítulo dinâmico).", "baixo", bool(relacionadas), nome, [v["id"]])

    # ---------------------------------------------------------------- modelo
    if modelo["lido"]:
        sem_fmt = [m for t in modelo["tabelas"].values() for m, d in t["medidas"].items() if not d["formato"]]
        if sem_fmt:
            a.add("M01", "Modelo e desempenho", "média" if len(sem_fmt) > 5 else "baixa", "[Nielsen 2] · L3",
                  "Medidas sem formato", f"{len(sem_fmt)} medida(s): {', '.join(sem_fmt[:6])}.",
                  "Definir formatString (milhar, %, casas decimais).", "baixo")
        for tn, t in modelo["tabelas"].items():
            if len(t["medidas"]) > 10:
                semp = [m for m, d in t["medidas"].items() if not d["pasta"]]
                if semp:
                    a.add("M02", "Modelo e desempenho", "baixa", "Organização do modelo",
                          f"Medidas sem pasta em {tn}", f"{len(semp)} de {len(t['medidas'])}: {', '.join(semp[:5])}.",
                          "Agrupar em displayFolders por tema (sem repetir pastas).", "baixo")
        nmed = sum(len(t["medidas"]) for t in modelo["tabelas"].values())
        sem_desc = sum(1 for t in modelo["tabelas"].values() for d in t["medidas"].values() if not d["descricao"])
        if nmed and sem_desc / nmed > 0.5:
            a.add("M03", "Modelo e desempenho", "baixa", "[Nielsen 10] Ajuda",
                  "Medidas sem descrição", f"{sem_desc} de {nmed} medidas.",
                  "Escrever descrições (aparecem ao passar o mouse e ajudam quem mantém o painel).", "médio")
        tem_data = any(t["data"] for t in modelo["tabelas"].values())
        if not tem_data and tempo_cols:
            a.add("M04", "Modelo e desempenho", "média", "Inteligência de tempo",
                  "Sem tabela de datas marcada",
                  f"Há colunas de tempo ({', '.join(f'{t}[{c}]' for t, c in sorted(tempo_cols)[:4])}) mas nenhuma "
                  "tabela marcada como tabela de datas.",
                  "Criar/marcar uma tabela calendário contínua e relacioná-la aos fatos.", "médio")
        bidir = [r for r in modelo["relacoes"] if str(r.get("crossFilteringBehavior", "")).lower() == "bothdirections"]
        if bidir:
            a.add("M07", "Modelo e desempenho", "baixa", "Desempenho e ambiguidade",
                  "Relacionamentos bidirecionais", f"{len(bidir)} relacionamento(s).",
                  "Usar filtro unidirecional e CROSSFILTER na medida quando necessário.", "médio")
        refs = medidas_referenciadas(modelo)
        orfas = [(t, m) for t, tab in modelo["tabelas"].items() for m, d in tab["medidas"].items()
                 if (t, m) not in cont and m not in refs and not d["oculta"]]
        if orfas:
            a.add("M05", "Modelo e desempenho", "baixa", "Oportunidade / limpeza",
                  "Medidas não usadas", f"{len(orfas)} medida(s) sem uso em visuais nem em outras medidas: "
                  + ", ".join(m for _, m in orfas[:8]) + ("…" if len(orfas) > 8 else "") + ".",
                  "Avaliar se viram nova visão (ver sugestões) ou se podem ser removidas/ocultadas.", "baixo")
    else:
        a.add("M00", "Modelo e desempenho", "baixa", "—",
              "Modelo semântico não lido",
              "Arquivo PBIX: o modelo é binário; campos foram inferidos dos visuais.",
              "Para análise completa (medidas não usadas, formatos, relacionamentos), salve como PBIP "
              "(Arquivo › Salvar como › .pbip) ou PBIT e envie de novo.", "baixo")
    return a.achados


def agrupar(achados):
    """Junta achados iguais (mesmo código/título/severidade) de páginas diferentes."""
    grupos = {}
    for x in achados:
        k = (x["codigo"], x["titulo"], x["severidade"])
        if k not in grupos:
            grupos[k] = dict(x, paginas=[x["pagina"]] if x["pagina"] else [], evidencias=[x["evidencia"]])
        else:
            g = grupos[k]
            if x["pagina"] and x["pagina"] not in g["paginas"]:
                g["paginas"].append(x["pagina"])
            g["evidencias"].append(x["evidencia"])
            g["visuais"] += x["visuais"]
    saida = []
    for g in grupos.values():
        if len(g["evidencias"]) > 1:
            exemplos = "; ".join(e.rstrip(".") for e in g["evidencias"][:4]) + (f"; e mais {len(g['evidencias']) - 4}"
                                                        if len(g["evidencias"]) > 4 else "")
            g["evidencia"] = f"{len(g['evidencias'])} ocorrências. {exemplos}"
        g["pagina"] = ", ".join(g["paginas"]) if g["paginas"] else None
        g["ocorrencias"] = len(g.pop("evidencias"))
        saida.append(g)
    return saida


def notas(achados):
    res = {}
    for c in CATEGORIAS:
        perda = sum(PESO[x["severidade"]] * (1 + 0.25 * min(x.get("ocorrencias", 1) - 1, 4))
                    for x in achados if x["categoria"] == c)
        res[c] = max(0, round(100 - perda))
    return res


# ============================================================================ novas visões
def nome_campo(t, c):
    return f"{t}[{c}]"


def sugerir_visoes(rel, modelo):
    cont, por_visual = usos(rel)
    dims = tabelas_dimensao(modelo)
    tabs = modelo["tabelas"]
    medidas = [(t, m) for t, tab in tabs.items() for m, d in tab["medidas"].items() if not d.get("oculta")]
    usadas_med = sorted([(t, m) for t, m in medidas if (t, m) in cont], key=lambda x: -cont[x])
    base = [x for x in usadas_med if classe_medida(x[1]) == "base"] or \
           [x for x in medidas if classe_medida(x[1]) == "base"]
    tempo = [(t, c) for t, tab in tabs.items() for c, d in tab["colunas"].items()
             if eh_tempo(c, d.get("tipo")) and not d.get("oculta") and not RE_ID.search(c)]
    tempo = [x for x in tempo if not re.search(r"atualiz|carga|refresh|modific|utc", sem_acento(x[1]))]
    tempo.sort(key=lambda x: (granularidade(x[1]), -cont[x]))
    categorias = [(t, c) for t in dims for c, d in tabs.get(t, {}).get("colunas", {}).items()
                  if not d.get("oculta") and not RE_ID.search(c) and not eh_tempo(c, d.get("tipo"))
                  and (d.get("tipo") in (None, "string"))]
    categorias.sort(key=lambda x: -cont[x])
    ids = [(t, c) for t in dims for c, d in tabs.get(t, {}).get("colunas", {}).items() if RE_ID.search(c)]
    def _entidade(t):
        return re.sub(r"^(dim|d_|tb_?)", "", sem_acento(t))
    ids.sort(key=lambda x: (-len(tabs[x[0]]["colunas"]), _entidade(x[0]) not in sem_acento(x[1]),
                            not sem_acento(x[1]).endswith("id"), x))
    paginas = rel["paginas"]
    pares_tempo = {(c["tabela"], c["campo"]) for _, v in por_visual
                   if any(eh_tempo(x["campo"]) for x in v["campos"] if x["papel"] in ("Category", "Axis"))
                   for c in v["campos"] if c["tipo"] == "Measure"}
    visoes = []

    def add(codigo, titulo, pergunta, principio, prioridade, visuais, motivo):
        visoes.append({"codigo": codigo, "titulo": titulo, "pergunta": pergunta, "principio": principio,
                       "prioridade": prioridade, "motivo": motivo, "visuais": visuais,
                       "automatizavel": all(v["tipo"] in SUPORTADOS_GERADOR for v in visuais)})

    t0 = tempo[0] if tempo else None
    d0 = categorias[0] if categorias else None

    # NV01 resumo executivo
    tem_resumo = any(sum(1 for v in p["visuais"] if v["tipo"] in TIPOS_CARTAO and v["y"] < 0.35 * p["altura"]) >= 2
                     for p in paginas)
    if not tem_resumo and base:
        kpis = base[:4]
        vis = [{"tipo": "card", "titulo": m, "campos": {"Values": nome_campo(t, m)}} for t, m in kpis]
        if t0:
            vis.append({"tipo": "lineChart", "titulo": f"Evolução de {kpis[0][1]}",
                        "campos": {"Category": nome_campo(*t0), "Y": nome_campo(*kpis[0])}})
        if d0:
            vis.append({"tipo": "clusteredBarChart", "titulo": f"{kpis[0][1]} por {d0[1]}",
                        "campos": {"Category": nome_campo(*d0), "Y": nome_campo(*kpis[0])}})
        add("NV01", "Resumo executivo", "Como estamos e onde agir, em 5 segundos?",
            "L1 História de 3 minutos · L6 · [Pirâmide]", "alta", vis,
            "O relatório não tem página inicial com KPIs; as medidas mais usadas viram os cartões.")

    # NV02 meta x realizado
    feitos = 0
    metas_usadas = set()
    campos_pagina = [{(c["tabela"], c["campo"]) for v in p["visuais"] for c in v["campos"]} for p in paginas]
    for t, m in base:
        if feitos >= 2:
            break
        tk = tokens(m)
        metas = [(tt, mm) for tt, mm in medidas if classe_medida(mm) == "meta" and tk & tokens(mm)
                 and (tt, mm) not in metas_usadas]
        if not metas:
            continue
        metas_usadas.add(metas[0])
        relacionadas_meta = {x for x in medidas if classe_medida(x[1]) == "meta" and tk & tokens(x[1])}
        if any(cp & relacionadas_meta and any(x in cp for x in medidas if tk & tokens(x[1])
                                              and classe_medida(x[1]) == "base") for cp in campos_pagina):
            continue  # meta já aparece ao lado de uma medida do mesmo tema
        varis = [(tt, mm) for tt, mm in medidas if classe_medida(mm) in ("variacao", "razao") and tk & tokens(mm)]
        vis = [{"tipo": "card", "titulo": m, "campos": {"Values": nome_campo(t, m)}},
               {"tipo": "card", "titulo": metas[0][1], "campos": {"Values": nome_campo(*metas[0])}}]
        vis += [{"tipo": "card", "titulo": mm, "campos": {"Values": nome_campo(tt, mm)}} for tt, mm in varis[:2]]
        if d0:
            vis.append({"tipo": "clusteredBarChart", "titulo": f"{m} × {metas[0][1]} por {d0[1]}",
                        "campos": {"Category": nome_campo(*d0), "Y": [nome_campo(t, m), nome_campo(*metas[0])]}})
        if t0:
            vis.append({"tipo": "lineChart", "titulo": f"{m} × {metas[0][1]} no tempo",
                        "campos": {"Category": nome_campo(*t0), "Y": [nome_campo(t, m), nome_campo(*metas[0])]}})
        add(f"NV02{chr(97 + feitos)}", f"Realizado × meta: {m}", f"{m} está acima ou abaixo da meta, e onde?",
            "L1 Contexto · L4 Foco no desvio · [IBCS]", "alta", vis,
            f"Existem {m} e {metas[0][1]} no modelo, mas nenhum visual os compara.")
        feitos += 1

    # NV03 tendência
    if t0:
        sem_tempo = [x for x in base if x not in pares_tempo][:3]
        if sem_tempo:
            vis = [{"tipo": "lineChart", "titulo": f"Evolução de {m}", "campos": {"Category": nome_campo(*t0),
                                                                              "Y": nome_campo(t, m)}}
                   for t, m in sem_tempo]
            add("NV03", "Tendências no tempo", "As principais medidas estão melhorando ou piorando?",
                "L2 Linha para tempo · [Shneiderman]", "média", vis,
                f"{', '.join(m for _, m in sem_tempo)} não aparecem ao longo de {t0[1]}.")

    # NV04 dimensões não exploradas
    nao_usadas = [x for x in categorias if x not in cont][:3]
    if nao_usadas and base:
        vis = [{"tipo": "clusteredBarChart", "titulo": f"{base[0][1]} por {c}",
                "campos": {"Category": nome_campo(t, c), "Y": nome_campo(*base[0])}} for t, c in nao_usadas]
        vis.append({"tipo": "tableEx", "titulo": "Detalhe",
                    "campos": {"Values": [nome_campo(*nao_usadas[0])] + [nome_campo(*b) for b in base[:3]]}})
        add("NV04", "Recortes ainda não explorados", "Há padrões por " + ", ".join(c for _, c in nao_usadas) + "?",
            "L1 Contexto · L2 Barras ordenadas", "média", vis,
            "Colunas de dimensão do modelo que não aparecem em nenhum visual.")

    # NV05 qualidade
    qual = [(t, m) for t, m in medidas if classe_medida(m) == "qualidade"]
    if qual:
        vis = [{"tipo": "card", "titulo": m, "campos": {"Values": nome_campo(t, m)}} for t, m in qual[:4]]
        if d0:
            vis.append({"tipo": "tableEx", "titulo": f"Pendências por {d0[1]}",
                        "campos": {"Values": [nome_campo(*d0)] + [nome_campo(t, m) for t, m in qual[:5]]}})
        add("NV05", "Qualidade dos dados e pendências", "O que está impedindo o número de ser confiável?",
            "L4 Foco no que exige ação · [Nielsen 9]", "média", vis,
            f"{len(qual)} medidas de pendência/validação no modelo; reuni-las orienta a correção na origem.")

    # NV06 drill-through
    tem_dt = any(p["tipo"] == "Drillthrough" for p in paginas)
    if ids and not tem_dt and base:
        t, c = ids[0]
        desc_cols = [x for x in categorias if x[0] == t][:3]
        vis = [{"tipo": "card", "titulo": m, "campos": {"Values": nome_campo(tt, m)}} for tt, m in base[:3]]
        vis.append({"tipo": "tableEx", "titulo": f"Ficha de {t}",
                    "campos": {"Values": [nome_campo(t, c)] + [nome_campo(*x) for x in desc_cols]
                               + [nome_campo(*b) for b in base[:3]]}})
        add("NV06", f"Ficha (drill-through) de {t}", f"Qual é a situação completa de um(a) {t} específico(a)?",
            "[Shneiderman] Detalhe sob demanda", "média", vis,
            f"{t}[{c}] identifica a entidade; uma página de drill-through tira detalhe das páginas gerenciais. "
            "Depois de gerar, configure o drill-through no Desktop (campo em 'Drill-through').")

    # NV07 pastas não exploradas
    por_pasta = defaultdict(list)
    for t, tab in tabs.items():
        for m, d in tab["medidas"].items():
            if d.get("pasta") and not d.get("oculta"):
                por_pasta[d["pasta"]].append((t, m))
    n = 0
    for pasta, ms in sorted(por_pasta.items()):
        if n >= 2 or not ms or any(x in cont for x in ms):
            continue
        vis = [{"tipo": "card", "titulo": m, "campos": {"Values": nome_campo(t, m)}} for t, m in ms[:4]]
        if d0:
            vis.append({"tipo": "clusteredBarChart", "titulo": f"{ms[0][1]} por {d0[1]}",
                        "campos": {"Category": nome_campo(*d0), "Y": nome_campo(*ms[0])}})
        add(f"NV07{chr(97 + n)}", f"Tema não explorado: {pasta}", f"O que as medidas de '{pasta}' mostram?",
            "L1 Contexto", "baixa", vis, f"Nenhuma das {len(ms)} medidas da pasta '{pasta}' está no relatório.")
        n += 1

    # NV08 relação entre medidas
    if len(base) >= 2 and d0:
        add("NV08", f"Relação entre {base[0][1]} e {base[1][1]}",
            f"Unidades com mais {base[0][1]} também têm mais {base[1][1]}?",
            "L2 Dispersão para relação", "baixa",
            [{"tipo": "scatterChart", "titulo": f"{base[0][1]} × {base[1][1]} por {d0[1]}",
              "campos": {"Category": nome_campo(*d0), "X": nome_campo(*base[0]), "Y": nome_campo(*base[1])}}],
            "Gráfico de dispersão revela atípicos; exige habilidade de dispersão no gerador (ver roadmap).")

    # NV09 tooltip
    if not any(p["tipo"] == "Tooltip" for p in paginas) and len(base) >= 2:
        add("NV09", "Página de dica de ferramenta", "Que contexto o usuário quer ao passar o mouse?",
            "L3 Menos desordem · [Shneiderman]", "baixa",
            [{"tipo": "card", "titulo": m, "campos": {"Values": nome_campo(t, m)}} for t, m in base[:3]],
            "Tooltip de página dá contexto sem ocupar espaço; configurar como Dica de ferramenta no Desktop.")
    return visoes


# ============================================================================ layout de specs
def layout_spec(visao, largura=1440):
    M, G = 24, 24
    cw = largura - 2 * M
    vis = [v for v in visao["visuais"] if v["tipo"] in SUPORTADOS_GERADOR]
    if not vis:
        return None
    out = [{"tipo": "textbox", "texto": visao["titulo"], "posicao": {"x": M, "y": 14, "largura": cw, "altura": 55}}]
    y = 84
    cards = [v for v in vis if v["tipo"] == "card"]
    graf = [v for v in vis if v["tipo"] not in ("card", "tableEx", "pivotTable", "slicer")]
    tabs = [v for v in vis if v["tipo"] in ("tableEx", "pivotTable")]
    for i in range(0, len(cards), 4):
        linha = cards[i:i + 4]
        w = (cw - (len(linha) - 1) * G) // len(linha)
        for j, v in enumerate(linha):
            out.append(dict(v, posicao={"x": M + j * (w + G), "y": y, "largura": w, "altura": 120}))
        y += 120 + G
    for i in range(0, len(graf), 2):
        linha = graf[i:i + 2]
        w = (cw - (len(linha) - 1) * G) // len(linha)
        for j, v in enumerate(linha):
            out.append(dict(v, posicao={"x": M + j * (w + G), "y": y, "largura": w, "altura": 340}))
        y += 340 + G
    for v in tabs:
        out.append(dict(v, posicao={"x": M, "y": y, "largura": cw, "altura": 360}))
        y += 360 + G
    altura = max(720, y)
    return {"pagina": {"nome": visao["titulo"][:100], "largura": largura, "altura": altura},
            "visuais": out}


# ============================================================================ relatório markdown
ICONE = {"alta": "🔴", "média": "🟠", "baixa": "🟡"}


def gerar_md(nome, formato, rel, modelo, achados, visoes, nts):
    L = []
    pags = rel["paginas"]
    nvis = sum(len(p["visuais"]) for p in pags)
    ntab = len(modelo["tabelas"])
    nmed = sum(len(t["medidas"]) for t in modelo["tabelas"].values())
    L.append(f"# Análise de upgrade — {nome}\n")
    L.append(f"Formato: **{formato}** · {len(pags)} páginas · {nvis} visuais · modelo: "
             + (f"{ntab} tabelas, {nmed} medidas, {len(modelo['relacoes'])} relacionamentos"
                if modelo["lido"] else "não lido (campos inferidos dos visuais)") + "\n")
    L.append("Referências: *Storytelling com Dados* (lições L1–L6), Few, Nielsen, Shneiderman, WCAG, IBCS. "
             "Índices são heurísticos (100 = nenhum achado na categoria) e servem para priorizar, não para "
             "dar nota ao trabalho.\n")
    L.append("## Índices por dimensão\n")
    L.append("| Dimensão | Índice | Achados |\n|---|---|---|")
    for c, n in nts.items():
        L.append(f"| {c} | {n} | {sum(1 for a in achados if a['categoria'] == c)} |")
    L.append("\n## Páginas\n")
    L.append("| # | Página | Tamanho | Visuais de dados | Segmentações | Uso |\n|---|---|---|---|---|---|")
    for i, p in enumerate(pags, 1):
        dados = [v for v in p["visuais"] if v["tipo"] not in TIPOS_DECORATIVOS | TIPOS_SEGMENTACAO]
        segs = [v for v in p["visuais"] if v["tipo"] in TIPOS_SEGMENTACAO]
        uso = p["tipo"] or ("oculta" if p["oculta"] else ("operacional" if eh_operacional(p) else "gerencial"))
        L.append(f"| {i} | {p['nome']} | {p['largura']}×{p['altura']} | {len(dados)} | {len(segs)} | {uso} |")

    ordem = {"alta": 0, "média": 1, "baixa": 2}
    L.append("\n## Melhorias sugeridas\n")
    L.append("Ordenadas por severidade. **Auto** = pode ser aplicada pelas skills sem edição manual no Desktop.\n")
    for i, a in enumerate(sorted(achados, key=lambda x: (ordem[x["severidade"]], x["codigo"])), 1):
        a["id"] = f"M{i:02d}"
        L.append(f"### {a['id']} {ICONE[a['severidade']]} {a['titulo']}"
                 + (f" — {a['pagina']}" if a["pagina"] else ""))
        L.append(f"- **Por quê:** {a['evidencia']}")
        L.append(f"- **O que fazer:** {a['recomendacao']}")
        L.append(f"- **Princípio:** {a['principio']} · **Esforço:** {a['esforco']} · "
                 f"**Auto:** {'sim' if a['automatizavel'] else 'não'} · `{a['codigo']}`\n")

    L.append("## Novas visões sugeridas\n")
    for v in visoes:
        L.append(f"### {v['codigo']} {ICONE[v['prioridade']]} {v['titulo']}")
        L.append(f"- **Pergunta que responde:** {v['pergunta']}")
        L.append(f"- **Por quê:** {v['motivo']}")
        L.append(f"- **Princípio:** {v['principio']} · **Auto:** {'sim' if v['automatizavel'] else 'parcial'}"
                 + (f" · spec: `specs/{v['codigo']}.json`" if v.get("spec") else ""))
        L.append("- **Visuais:**")
        for x in v["visuais"]:
            campos = "; ".join(f"{k}: {', '.join(c) if isinstance(c, list) else c}" for k, c in x["campos"].items())
            L.append(f"  - {x['tipo']} — {x['titulo']} ({campos})")
        L.append("")

    L.append("## Títulos atuais (para reescrever como títulos de ação)\n")
    for p in pags:
        tits = [v["titulo"] or v["texto"] for v in p["visuais"] if (v["titulo"] or v["texto"])]
        if tits:
            L.append(f"- **{p['nome']}:** " + " · ".join(f"“{t[:80]}”" for t in tits[:12]))
    L.append("\n## Perguntas de contexto (L1)\n")
    L.append("1. Quem usa o painel e que decisão toma com ele?")
    L.append("2. Qual é a grande ideia que a primeira página precisa transmitir?")
    L.append("3. Com que frequência é consultado e em qual tela (monitor, projetor, celular)?")
    L.append("4. Quais páginas são de conferência/exportação e podem continuar densas?")
    return "\n".join(L) + "\n"


# ============================================================================ comandos
def analisar(entrada, saida=None):
    itens = carregar(entrada)
    resultados = []
    for nome, formato, rel, modelo in itens:
        destino = Path(saida or f"analise_{re.sub(r'[^A-Za-z0-9_-]+', '_', nome)}")
        if len(itens) > 1:
            destino = destino / re.sub(r"[^A-Za-z0-9_-]+", "_", nome)
        destino.mkdir(parents=True, exist_ok=True)
        achados = agrupar(auditar(rel, modelo))
        visoes = sugerir_visoes(rel, modelo)
        larguras = Counter(p["largura"] for p in rel["paginas"] if not eh_operacional(p))
        largura = larguras.most_common(1)[0][0] if larguras else 1440
        largura = largura if 1280 <= largura <= 1920 else 1440
        specs = destino / "specs"
        if specs.exists():
            shutil.rmtree(specs)
        for v in visoes:
            if modelo["lido"] and v["automatizavel"]:
                sp = layout_spec(v, largura)
                if sp:
                    specs.mkdir(exist_ok=True)
                    (specs / f"{v['codigo']}.json").write_text(json.dumps(sp, ensure_ascii=False, indent=2) + "\n",
                                                               encoding="utf-8")
                    v["spec"] = True
        nts = notas(achados)
        md = gerar_md(nome, formato, rel, modelo, achados, visoes, nts)
        inventario = {"nome": nome, "formato": formato, "origem": str(entrada), "relatorio": rel,
                      "modelo": {**modelo, "tabelas": {k: {**t} for k, t in modelo["tabelas"].items()}}}
        (destino / "inventario.json").write_text(json.dumps(inventario, ensure_ascii=False, indent=1, default=list),
                                                 encoding="utf-8")
        (destino / "analise.json").write_text(json.dumps({"indices": nts, "melhorias": achados,
                                                          "novas_visoes": visoes}, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
        (destino / "relatorio.md").write_text(md, encoding="utf-8")
        cont = Counter(a["severidade"] for a in achados)
        print(f"{nome} [{formato}]: {len(rel['paginas'])} páginas, {len(achados)} melhorias "
              f"(alta {cont['alta']}, média {cont['média']}, baixa {cont['baixa']}), "
              f"{len(visoes)} novas visões → {destino / 'relatorio.md'}")
        resultados.append(destino)
    return resultados


def comparar(antes, depois):
    def assinatura(entrada):
        _, _, rel, modelo = carregar(entrada)[0]
        pags = {p["id"]: p for p in rel["paginas"]}
        meds = {(t, m) for t, tab in modelo["tabelas"].items() for m in tab["medidas"]}
        return pags, meds
    pa, ma = assinatura(antes)
    pd, md = assinatura(depois)
    print("Páginas adicionadas:", [pd[i]["nome"] for i in pd if i not in pa] or "nenhuma")
    print("Páginas removidas:  ", [pa[i]["nome"] for i in pa if i not in pd] or "nenhuma")
    for pid in pa.keys() & pd.keys():
        va = {v["id"]: v for v in pa[pid]["visuais"]}
        vd = {v["id"]: v for v in pd[pid]["visuais"]}
        rem = [i for i in va if i not in vd]
        add = [i for i in vd if i not in va]
        mud = [i for i in va.keys() & vd.keys()
               if [(c["tabela"], c["campo"]) for c in va[i]["campos"]] != [(c["tabela"], c["campo"]) for c in vd[i]["campos"]]]
        if rem or add or mud:
            print(f"[{pd[pid]['nome']}] +{len(add)} visuais, -{len(rem)} visuais, {len(mud)} com campos alterados")
    print("Medidas adicionadas:", sorted(m for _, m in md - ma) or "nenhuma")
    print("Medidas removidas:  ", sorted(m for _, m in ma - md) or "nenhuma")
    if any(i not in pd for i in pa) or ma - md:
        print("\nATENÇÃO: houve remoções. Confirme que eram intencionais antes de entregar.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analisar")
    a.add_argument("entrada")
    a.add_argument("--saida")
    a = sub.add_parser("comparar")
    a.add_argument("antes")
    a.add_argument("depois")
    args = ap.parse_args()
    try:
        if args.cmd == "analisar":
            analisar(args.entrada, args.saida)
        else:
            comparar(args.antes, args.depois)
    except (ValueError, zipfile.BadZipFile, OSError) as e:
        print(f"ERRO  {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
