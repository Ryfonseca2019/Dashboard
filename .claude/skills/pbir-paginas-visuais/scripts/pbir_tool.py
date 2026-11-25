#!/usr/bin/env python3
"""Ferramenta para evoluir relatórios Power BI em formato PBIP/PBIR.

Comandos:
  campos  <projeto> [--busca TEXTO] [--tabela NOME]   lista tabelas, colunas e medidas do modelo (TMDL)
  criar   <projeto> <spec.json> [--simular]            cria página nova ou adiciona visuais a uma página existente
  validar <projeto>                                    confere estrutura, IDs e referências de campos
  medida  <projeto> --tabela T --nome N --expressao DAX [--formato F] [--pasta P] [--descricao D]
  formatar <projeto> <formatos.json>   aplica opções a visuais existentes ({"<id visual>": {opções}})
  trocar-tipo <projeto> <id visual> <novo tipo>   ex.: pizza → clusteredBarChart, gauge → card
  alinhar <projeto> [--pagina P] [--tolerancia 8] encaixa bordas quase alinhadas
  layout  <projeto> <layout.json>      reposiciona ({"<id visual>": {"x":..,"y":..,"largura":..,"altura":..}})
  paginas <projeto> [--ordem a,b] [--renomear id=Nome] [--ocultar P] [--mostrar P] [--ativa P]
  tema    <projeto> [--nome N] [--destaque #hex] [--titulo #hex] [--fundo #hex] [--arquivo tema.json]
  navegacao <projeto> --posicao x,y,larg,alt [--paginas a,b]   navegador de páginas nas páginas indicadas
  ajustar <projeto> [--pagina ID|nome] [--ordem-leitura] [--texto-alt] [--titulos titulos.json] [--simular]
          corrige visuais existentes: z/tabOrder na ordem de leitura, texto alternativo a partir do título,
          e títulos novos ({"<id do visual>": "Título de ação", ...})

<projeto> pode ser a pasta que contém o .pbip, a pasta *.Report ou o próprio arquivo .pbip.
"""
import argparse
import json
import os
import re
import secrets
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pbir_recursos as R  # noqa: E402

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
    "scatterChart": ["Category", "Series", "X", "Y", "Size", "Tooltips"],
    "lineClusteredColumnComboChart": ["Category", "ColumnY", "Y", "Series", "Tooltips"],
    "textbox": [],
    "actionButton": [],
    "pageNavigator": [],
}
SEM_CAMPOS = {"textbox", "actionButton", "pageNavigator"}
APELIDOS = {"cartao": "card", "segmentacao": "slicer", "tabela": "tableEx", "matriz": "pivotTable",
            "barras": "clusteredBarChart", "colunas": "clusteredColumnChart", "linha": "lineChart",
            "rosca": "donutChart", "texto": "textbox", "titulo": "textbox", "combo": "lineClusteredColumnComboChart",
            "dispersao": "scatterChart"}


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
    """Retorna {tabela: {"colunas": {nome: dataType}, "medidas": set}}."""
    tabelas = {}
    if modelo is None:
        return tabelas
    for arq in sorted((modelo / "definition").rglob("*.tmdl")):
        atual = None
        for linha in arq.read_text(encoding="utf-8-sig").splitlines():
            m = RE_TABELA.match(linha)
            if m:
                atual = tabelas.setdefault(_nome(m), {"colunas": {}, "medidas": set()})
                ultima_coluna = None
                continue
            if linha and not linha[0].isspace():
                atual = None  # outro objeto de nível superior (relationship, expression...)
                continue
            if atual is None:
                continue
            m = RE_COLUNA.match(linha)
            if m:
                ultima_coluna = _nome(m)
                atual["colunas"][ultima_coluna] = None
                continue
            m = RE_MEDIDA.match(linha)
            if m:
                ultima_coluna = None
                atual["medidas"].add(_nome(m))
                continue
            if re.match(r"^(?:\t|    )\S", linha):
                ultima_coluna = None
            md = re.match(r"^(?:\t\t|        )dataType:\s*(\S+)", linha)
            if md and ultima_coluna:
                atual["colunas"][ultima_coluna] = md.group(1)
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


def montar_visual(spec, nome, z, schema, tabelas, ctx=None):
    """ctx: {"criar_medida": fn, "paginas": {nome: id}, "avisos": []} para recursos avançados."""
    ctx = ctx or {"criar_medida": _sem_medida, "paginas": {}, "avisos": []}
    spec = R.expandir(spec, tabelas, lambda r: resolver_campo(r, tabelas), ctx["criar_medida"])
    tipo = APELIDOS.get(spec["tipo"], spec["tipo"])
    if tipo not in PAPEIS:
        raise Erro(f"Tipo de visual '{spec['tipo']}' não suportado. Use: {', '.join(PAPEIS)}")
    pos = spec.get("posicao") or {}
    for k in ("x", "y", "largura", "altura"):
        if k not in pos:
            raise Erro(f"Visual '{spec.get('titulo', tipo)}': posicao.{k} obrigatório")
    visual = {"visualType": tipo}

    if tipo == "actionButton":
        return _envelope(schema, nome, pos, z, R.montar_botao(spec, ctx["paginas"]))
    if tipo == "pageNavigator":
        return _envelope(schema, nome, pos, z, R.montar_navegador())
    campos = spec.get("campos", {})
    if tipo not in SEM_CAMPOS:
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
    elif tipo in ("clusteredBarChart", "clusteredColumnChart", "lineChart", "donutChart", "scatterChart",
                  "lineClusteredColumnComboChart"):
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
    v = _envelope(schema, nome, pos, z, visual)
    ctx["avisos"] += R.aplicar_opcoes(v, spec, tabelas, lambda r: resolver_campo(r, tabelas),
                                      ctx["criar_medida"], ctx["paginas"])
    return v


def _envelope(schema, nome, pos, z, visual):
    return {
        "$schema": schema,
        "name": nome,
        "position": {"x": pos["x"], "y": pos["y"], "width": pos["largura"], "height": pos["altura"],
                     "z": z, "tabOrder": z},
        "visual": visual,
    }


def _sem_medida(*_a, **_k):
    raise Erro("Este recurso cria medidas; use pelo comando criar/formatar com o projeto carregado")


def contexto(report, modelo, tabelas, simular, criadas):
    """Callbacks para recursos que criam medidas no TMDL e referenciam páginas por nome."""
    paginas = {}
    pdir = report / "definition" / "pages"
    for pj in pdir.glob("*/page.json"):
        paginas[ler_json(pj).get("displayName")] = pj.parent.name

    def criar_medida(tab, nome, expr, formato, pasta, descricao):
        r = R.adicionar_medida(modelo, tab, nome, expr, formato, pasta, descricao, tabelas, simular)
        if r == "criada":
            criadas.append(f"{tab}[{nome}]")
    return {"criar_medida": criar_medida, "paginas": paginas, "avisos": []}


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
    criadas = []
    ctx = contexto(report, modelo, tabelas, args.simular, criadas)
    for m in spec.get("medidas", []):
        r = R.adicionar_medida(modelo, m["tabela"], m["nome"], m["expressao"], m.get("formato"), m.get("pasta"),
                               m.get("descricao"), tabelas, args.simular)
        if r == "criada":
            criadas.append(f"{m['tabela']}[{m['nome']}]")
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
        especial = R.configurar_pagina_especial(pagina, pspec, lambda r: resolver_campo(r, tabelas))
        if especial == "drillthrough" and not pspec.get("sem_voltar"):
            spec = dict(spec, visuais=list(spec.get("visuais", [])) + [{
                "tipo": "botao", "acao": "voltar",
                "posicao": {"x": pagina["width"] - 24 - 140, "y": 22, "largura": 140, "altura": 40}}])
        ctx["paginas"][nome_exibicao] = pid
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
        v = montar_visual(vs, vid, z, schema_visual, tabelas, ctx)
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
    finalizar(report, modelo, criadas, ctx["avisos"], args.simular)


def finalizar(report, modelo, criadas, avisos, simular):
    for m in criadas:
        print(f"{'[simulação] criaria' if simular else 'medida criada'} {m} (DAX: conferir no Desktop)")
    for a in dict.fromkeys(avisos):
        print(f"NOTA  {a}")
    if not simular:
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
    # referências entre páginas, tema e drill-through
    ids_paginas = set(pastas)
    rj = report / "definition" / "report.json"
    if rj.exists():
        rep = ler_json(rj)
        ct = (rep.get("themeCollection") or {}).get("customTheme")
        if ct and ct.get("type") == "RegisteredResources" and \
                not (report / "StaticResources" / "RegisteredResources" / ct["name"]).exists():
            erro(f"Tema customizado '{ct['name']}' não está em StaticResources/RegisteredResources")
    for pid in pastas:
        pj = paginas_dir / pid / "page.json"
        if not pj.exists():
            continue
        pagina = ler_json(pj)
        filtros = {f.get("name") for f in (pagina.get("filterConfig") or {}).get("filters", [])}
        for par in (pagina.get("pageBinding") or {}).get("parameters", []):
            if par.get("boundFilter") and par["boundFilter"] not in filtros:
                erro(f"[{pagina.get('displayName')}] drill-through aponta para filtro inexistente {par['boundFilter']}")
        for tipo, ent, prop in iterar_campos(pagina):
            if tabelas and (ent not in tabelas or prop not in (tabelas[ent]["medidas"] if tipo == "Measure"
                                                                 else tabelas[ent]["colunas"])):
                erro(f"[{pagina.get('displayName')}] filtro/drill-through usa campo inexistente {ent}[{prop}]")
        for vj in (paginas_dir / pid).glob("visuals/*/visual.json"):
            vco = ler_json(vj).get("visual", {}).get("visualContainerObjects", {})
            refs = []
            for k in ("navigationSection", "drillthroughSection"):
                refs.append(((vco.get("visualLink") or [{}])[0].get("properties", {}).get(k)))
            refs.append(((vco.get("visualTooltip") or [{}])[0].get("properties", {}).get("section")))
            for r in refs:
                alvo_pid = (r or {}).get("expr", {}).get("Literal", {}).get("Value", "").strip("'")
                if alvo_pid and alvo_pid not in ids_paginas:
                    erro(f"[{pagina.get('displayName')}] visual {vj.parent.name} aponta para página inexistente {alvo_pid}")
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


def _titulo_atual(v):
    try:
        val = v["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]
        return val[1:-1].replace("''", "'")
    except (KeyError, IndexError, TypeError):
        return None


def cmd_ajustar(args):
    report, modelo = localizar(args.projeto)
    paginas_dir = report / "definition" / "pages"
    titulos = ler_json(Path(args.titulos)) if args.titulos else {}
    alvo = args.pagina
    mudou = 0
    usados_titulos = set()
    for pj in sorted(paginas_dir.glob("*/page.json")):
        pagina = ler_json(pj)
        if alvo and alvo not in (pj.parent.name, pagina.get("displayName")):
            continue
        arquivos = sorted(pj.parent.glob("visuals/*/visual.json"))
        visuais = [(f, ler_json(f)) for f in arquivos]
        alterados = set()
        if args.ordem_leitura:
            ordem = sorted(visuais, key=lambda fv: (round(fv[1].get("position", {}).get("y", 0) / 20),
                                                    fv[1].get("position", {}).get("x", 0)))
            for i, (f, v) in enumerate(ordem):
                pos = v.setdefault("position", {})
                if pos.get("z") != i or pos.get("tabOrder") != i:
                    pos["z"], pos["tabOrder"] = i, i
                    alterados.add(f)
        for f, v in visuais:
            vid = v.get("name")
            vis = v.get("visual")
            if vis is None:
                continue
            vco = vis.setdefault("visualContainerObjects", {})
            if vid in titulos:
                usados_titulos.add(vid)
                props = vco.setdefault("title", [{"properties": {}}])[0].setdefault("properties", {})
                props["text"] = texto(titulos[vid])
                props["show"] = lit("true")
                alterados.add(f)
            if args.texto_alt and vis.get("visualType") not in ("textbox", "shape", "image", "actionButton"):
                geral = vco.setdefault("general", [{"properties": {}}])[0].setdefault("properties", {})
                if "altText" not in geral:
                    base = titulos.get(vid) or _titulo_atual(v)
                    if base:
                        geral["altText"] = texto(base)
                        alterados.add(f)
        for f, v in visuais:
            if f in alterados:
                mudou += 1
                if args.simular:
                    print(f"[simulação] alteraria {f.relative_to(report)}")
                else:
                    gravar_json(f, v)
    faltando = set(titulos) - usados_titulos
    if faltando:
        print("AVISO títulos para visuais não encontrados: " + ", ".join(sorted(faltando)))
    print(f"{mudou} visual(is) {'seriam alterados' if args.simular else 'alterados'}")
    if not args.simular:
        problemas = validar(report, modelo)
        imprimir_problemas(problemas)
        if any(n == "ERRO" for n, _ in problemas):
            sys.exit(1)


def _paginas(report, filtro=None):
    pdir = report / "definition" / "pages"
    for pj in sorted(pdir.glob("*/page.json")):
        pagina = ler_json(pj)
        if filtro and filtro not in (pj.parent.name, pagina.get("displayName")):
            continue
        yield pj, pagina, [(f, ler_json(f)) for f in sorted(pj.parent.glob("visuals/*/visual.json"))]


def _achar_visual(report, vid):
    for pj, pagina, visuais in _paginas(report):
        for f, v in visuais:
            if v.get("name") == vid or f.parent.name == vid:
                return pj, pagina, f, v
    raise Erro(f"Visual '{vid}' não encontrado")


def _id_pagina(report, ref):
    for pj, pagina, _ in _paginas(report):
        if ref in (pj.parent.name, pagina.get("displayName")):
            return pj.parent.name
    raise Erro(f"Página '{ref}' não encontrada")


def _fim(report, modelo, simular, n, criadas=None, avisos=None):
    print(f"{n} arquivo(s) {'seriam alterados' if simular else 'alterados'}")
    finalizar(report, modelo, criadas or [], avisos or [], simular)


def cmd_medida(args):
    report, modelo = localizar(args.projeto)
    tabelas = ler_modelo(modelo)
    expr = Path(args.expressao[1:]).read_text(encoding="utf-8") if args.expressao.startswith("@") else args.expressao
    r = R.adicionar_medida(modelo, args.tabela, args.nome, expr, args.formato, args.pasta, args.descricao,
                           tabelas, args.simular)
    print(f"medida {args.tabela}[{args.nome}]: {r}")
    finalizar(report, modelo, [], [], args.simular)


def cmd_formatar(args):
    report, modelo = localizar(args.projeto)
    tabelas = ler_modelo(modelo)
    criadas = []
    ctx = contexto(report, modelo, tabelas, args.simular, criadas)
    n = 0
    for vid, opcoes in ler_json(Path(args.formatos)).items():
        _, _, f, v = _achar_visual(report, vid)
        if "titulo" in opcoes:
            props = v["visual"].setdefault("visualContainerObjects", {}).setdefault(
                "title", [{"properties": {}}])[0].setdefault("properties", {})
            props["text"], props["show"] = texto(opcoes["titulo"]), lit("true")
        ctx["avisos"] += R.aplicar_opcoes(v, dict(opcoes, _formatar=True), tabelas,
                                          lambda r: resolver_campo(r, tabelas),
                                          ctx["criar_medida"], ctx["paginas"], ordem_padrao=False)
        n += 1
        if not args.simular:
            gravar_json(f, v)
    _fim(report, modelo, args.simular, n, criadas, ctx["avisos"])


def cmd_trocar_tipo(args):
    report, modelo = localizar(args.projeto)
    tabelas = ler_modelo(modelo)
    novo = APELIDOS.get(args.novo, args.novo)
    _, _, f, v = _achar_visual(report, args.visual)
    antigo, descartados = R.trocar_tipo(v, novo)
    R.aplicar_opcoes(v, {}, tabelas, lambda r: resolver_campo(r, tabelas), _sem_medida)
    print(f"{args.visual}: {antigo} → {novo}" + (f" (papéis descartados: {', '.join(descartados)})" if descartados else ""))
    if not args.simular:
        gravar_json(f, v)
    _fim(report, modelo, args.simular, 1)


def cmd_alinhar(args):
    report, modelo = localizar(args.projeto)
    n = 0
    for pj, pagina, visuais in _paginas(report, args.pagina):
        vs = [v for _, v in visuais]
        m = R.alinhar(vs, pagina.get("width", 1280), pagina.get("height", 720), args.tolerancia)
        if m:
            print(f"[{pagina.get('displayName')}] {m} visual(is) alinhados")
            n += m
            if not args.simular:
                for f, v in visuais:
                    gravar_json(f, v)
    _fim(report, modelo, args.simular, n)


def cmd_layout(args):
    report, modelo = localizar(args.projeto)
    n = 0
    for vid, pos in ler_json(Path(args.layout)).items():
        pj, pagina, f, v = _achar_visual(report, vid)
        p = v.setdefault("position", {})
        for k, kk in (("x", "x"), ("y", "y"), ("largura", "width"), ("altura", "height")):
            if k in pos:
                p[kk] = pos[k]
        W, H = pagina.get("width", 1280), pagina.get("height", 720)
        if p["x"] < 0 or p["y"] < 0 or p["x"] + p["width"] > W or p["y"] + p["height"] > H:
            raise Erro(f"{vid} sairia da página {W}x{H}: {p}")
        n += 1
        if not args.simular:
            gravar_json(f, v)
    _fim(report, modelo, args.simular, n)


def cmd_paginas(args):
    report, modelo = localizar(args.projeto)
    pj_meta = report / "definition" / "pages" / "pages.json"
    meta = ler_json(pj_meta)
    n = 0
    if args.ordem:
        primeiros = [_id_pagina(report, x.strip()) for x in args.ordem.split(",") if x.strip()]
        meta["pageOrder"] = primeiros + [p for p in meta["pageOrder"] if p not in primeiros]
        n += 1
    if args.ativa:
        meta["activePageName"] = _id_pagina(report, args.ativa)
        n += 1
    alteracoes = {}
    for r in args.renomear or []:
        ref, _, nome = r.partition("=")
        alteracoes.setdefault(_id_pagina(report, ref), {})["displayName"] = nome
    for ref in args.ocultar or []:
        alteracoes.setdefault(_id_pagina(report, ref), {})["visibility"] = "HiddenInViewMode"
    for ref in args.mostrar or []:
        alteracoes.setdefault(_id_pagina(report, ref), {})["visibility"] = None
    for pid, mud in alteracoes.items():
        f = report / "definition" / "pages" / pid / "page.json"
        pagina = ler_json(f)
        for k, val in mud.items():
            if val is None:
                pagina.pop(k, None)
            else:
                pagina[k] = val
        n += 1
        if not args.simular:
            gravar_json(f, pagina)
    if not args.simular and (args.ordem or args.ativa):
        gravar_json(pj_meta, meta)
    _fim(report, modelo, args.simular, n)


def cmd_tema(args):
    report, modelo = localizar(args.projeto)
    if args.arquivo:
        tema = ler_json(Path(args.arquivo))
    else:
        tema = R.tema_padrao(args.nome or "Tema Storytelling", args.destaque or R.DESTAQUE,
                             args.titulo or COR_TITULO, args.fundo or COR_FUNDO_PAGINA)
    destino = R.aplicar_tema(report, tema, args.simular)
    print(f"tema '{tema.get('name')}' → {destino.relative_to(report)}")
    _fim(report, modelo, args.simular, 2)


def cmd_navegacao(args):
    report, modelo = localizar(args.projeto)
    x, y, w, h = (int(v) for v in args.posicao.split(","))
    alvo = {_id_pagina(report, p.strip()) for p in args.paginas.split(",")} if args.paginas else None
    schema = schema_mais_usado(report / "definition" / "pages", "visual.json", SCHEMA_VISUAL_PADRAO)
    usados = ids_existentes(report / "definition" / "pages")
    n = 0
    for pj, pagina, visuais in _paginas(report):
        pid = pj.parent.name
        if (alvo and pid not in alvo) or (not alvo and (pagina.get("type") or pagina.get("visibility"))):
            continue
        if any(v.get("visual", {}).get("visualType") == "pageNavigator" for _, v in visuais):
            continue
        novo = {"x": x, "y": y, "width": w, "height": h}
        W, H = pagina.get("width", 1280), pagina.get("height", 720)
        if x < 0 or y < 0 or x + w > W or y + h > H:
            print(f"PULADA [{pagina.get('displayName')}]: posição fora da página {W}x{H}")
            continue
        conflito = [v.get("name") for _, v in visuais if v.get("position") and R._sobrepoe(novo, v["position"])]
        if conflito:
            print(f"PULADA [{pagina.get('displayName')}]: sobrepõe {', '.join(conflito[:3])}; "
                  "libere espaço (layout) ou escolha outra --posicao")
            continue
        z = 1 + max([v.get("position", {}).get("z", 0) for _, v in visuais] or [-1])
        vid = novo_id(usados)
        v = _envelope(schema, vid, {"x": x, "y": y, "largura": w, "altura": h}, z, R.montar_navegador())
        n += 1
        if not args.simular:
            gravar_json(pj.parent / "visuals" / vid / "visual.json", v)
    _fim(report, modelo, args.simular, n)


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
    a = sub.add_parser("medida")
    a.add_argument("projeto")
    a.add_argument("--tabela", required=True)
    a.add_argument("--nome", required=True)
    a.add_argument("--expressao", required=True, help="DAX ou @arquivo.dax")
    a.add_argument("--formato")
    a.add_argument("--pasta")
    a.add_argument("--descricao")
    a.add_argument("--simular", action="store_true")
    a.set_defaults(func=cmd_medida)
    a = sub.add_parser("formatar")
    a.add_argument("projeto")
    a.add_argument("formatos")
    a.add_argument("--simular", action="store_true")
    a.set_defaults(func=cmd_formatar)
    a = sub.add_parser("trocar-tipo")
    a.add_argument("projeto")
    a.add_argument("visual")
    a.add_argument("novo")
    a.add_argument("--simular", action="store_true")
    a.set_defaults(func=cmd_trocar_tipo)
    a = sub.add_parser("alinhar")
    a.add_argument("projeto")
    a.add_argument("--pagina")
    a.add_argument("--tolerancia", type=int, default=8)
    a.add_argument("--simular", action="store_true")
    a.set_defaults(func=cmd_alinhar)
    a = sub.add_parser("layout")
    a.add_argument("projeto")
    a.add_argument("layout")
    a.add_argument("--simular", action="store_true")
    a.set_defaults(func=cmd_layout)
    a = sub.add_parser("paginas")
    a.add_argument("projeto")
    a.add_argument("--ordem")
    a.add_argument("--ativa")
    a.add_argument("--renomear", action="append")
    a.add_argument("--ocultar", action="append")
    a.add_argument("--mostrar", action="append")
    a.add_argument("--simular", action="store_true")
    a.set_defaults(func=cmd_paginas)
    a = sub.add_parser("tema")
    a.add_argument("projeto")
    a.add_argument("--nome")
    a.add_argument("--destaque")
    a.add_argument("--titulo")
    a.add_argument("--fundo")
    a.add_argument("--arquivo")
    a.add_argument("--simular", action="store_true")
    a.set_defaults(func=cmd_tema)
    a = sub.add_parser("navegacao")
    a.add_argument("projeto")
    a.add_argument("--posicao", required=True)
    a.add_argument("--paginas")
    a.add_argument("--simular", action="store_true")
    a.set_defaults(func=cmd_navegacao)
    a = sub.add_parser("ajustar")
    a.add_argument("projeto")
    a.add_argument("--pagina")
    a.add_argument("--ordem-leitura", action="store_true")
    a.add_argument("--texto-alt", action="store_true")
    a.add_argument("--titulos")
    a.add_argument("--simular", action="store_true")
    a.set_defaults(func=cmd_ajustar)
    a = sub.add_parser("validar")
    a.add_argument("projeto")
    a.set_defaults(func=cmd_validar)
    args = ap.parse_args()
    try:
        args.func(args)
    except (Erro, R.ErroRecurso) as e:
        print(f"ERRO  {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
