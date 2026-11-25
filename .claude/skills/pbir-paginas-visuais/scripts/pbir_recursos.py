"""Recursos avançados do pbir_tool: medidas TMDL, visuais avançados, destaque, navegação,
páginas especiais, alinhamento, troca de tipo de visual e tema corporativo.

Este módulo é importado por pbir_tool.py; não execute diretamente.
"""
import json
import re
import secrets
import uuid
from collections import Counter
from pathlib import Path

# Paleta Storytelling com Dados: base neutra + uma cor de destaque + status sem vermelho/verde
DESTAQUE = "#0072CE"
NEUTRO = "#BFC5CC"
ALERTA = "#D9822B"
TEXTO_SECUNDARIO = "#5A6B7B"


class ErroRecurso(Exception):
    pass


# =========================================================================== expressões PBIR
def lit(valor):
    return {"expr": {"Literal": {"Value": valor}}}


def texto(s):
    return lit("'" + str(s).replace("'", "''") + "'")


def num(n):
    return lit(f"{n}D")


def cor(hexa):
    return {"solid": {"color": lit(f"'{hexa}'")}}


def campo_expr(tipo, tabela, campo):
    return {tipo: {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": campo}}


def valor_literal(v, tipo_coluna):
    """Literal de filtro: inteiro → 2025L, decimal → 1.5D, texto → 'x'."""
    t = (tipo_coluna or "").lower()
    if isinstance(v, bool):
        return {"Literal": {"Value": "true" if v else "false"}}
    if t in ("int64", "integer", "whole") or (isinstance(v, int) and t not in ("string",)):
        return {"Literal": {"Value": f"{int(v)}L"}}
    if t in ("double", "decimal") or isinstance(v, float):
        return {"Literal": {"Value": f"{float(v)}D"}}
    return {"Literal": {"Value": "'" + str(v).replace("'", "''") + "'"}}


def novo_nome():
    return secrets.token_hex(10)


# =========================================================================== TMDL: medidas
def _nome_tmdl(nome):
    return nome if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", nome) else "'" + nome.replace("'", "''") + "'"


def _arquivo_tabela(modelo_dir: Path, tabela):
    alvo = re.compile(r"^table\s+(?:'" + re.escape(tabela.replace("'", "''")) + r"'|" + re.escape(tabela) + r")\s*$")
    for arq in sorted((modelo_dir / "definition").rglob("*.tmdl")):
        for linha in arq.read_text(encoding="utf-8-sig").splitlines():
            if alvo.match(linha.rstrip()):
                return arq
    return None


def adicionar_medida(modelo_dir: Path, tabela, nome, expressao, formato=None, pasta=None, descricao=None,
                     tabelas=None, simular=False):
    """Insere uma medida na tabela (arquivo TMDL). Retorna 'criada' ou 'existente'."""
    if modelo_dir is None:
        raise ErroRecurso("Modelo semântico não localizado; não é possível criar medidas.")
    if tabelas is not None:
        if tabela not in tabelas:
            raise ErroRecurso(f"Tabela '{tabela}' não existe no modelo")
        if nome in tabelas[tabela]["medidas"]:
            return "existente"
        todas = {m for t in tabelas.values() for m in t["medidas"]} | {c for t in tabelas.values() for c in t["colunas"]}
        if nome in todas:
            raise ErroRecurso(f"Já existe medida/coluna chamada '{nome}' em outra tabela")
    arq = _arquivo_tabela(modelo_dir, tabela)
    if arq is None:
        raise ErroRecurso(f"Arquivo TMDL da tabela '{tabela}' não encontrado (modelo em model.bim não é suportado)")
    linhas = arq.read_text(encoding="utf-8-sig").splitlines()
    inicio = next(i for i, l in enumerate(linhas) if l.startswith("table "))
    pos = len(linhas)
    for i in range(inicio + 1, len(linhas)):
        l = linhas[i]
        if l and not l[0].isspace():
            pos = i
            break
        if re.match(r"^\t(measure|column|partition|hierarchy|annotation|calculationGroup)\b", l) or \
                re.match(r"^\t///", l):
            pos = i
            break
    bloco = []
    if descricao:
        bloco += [f"\t/// {d}" for d in str(descricao).splitlines()]
    corpo = [x.rstrip() for x in str(expressao).strip().splitlines()]
    bloco.append(f"\tmeasure {_nome_tmdl(nome)} =")
    bloco += [f"\t\t\t{x.strip()}" if x.strip() else "" for x in corpo]
    if formato:
        bloco.append(f"\t\tformatString: {formato}")
    if pasta:
        bloco.append(f"\t\tdisplayFolder: {pasta}")
    bloco.append(f"\t\tlineageTag: {uuid.uuid4()}")
    bloco.append("")
    novo = linhas[:pos] + bloco + linhas[pos:]
    if not simular:
        arq.write_text("\n".join(novo) + "\n", encoding="utf-8")
    if tabelas is not None:
        tabelas[tabela]["medidas"].add(nome)
    return "criada"


def nome_unico(base, tabelas):
    existentes = {m for t in tabelas.values() for m in t["medidas"]} | \
                 {c for t in tabelas.values() for c in t["colunas"]}
    nome, i = base, 2
    while nome in existentes:
        nome, i = f"{base} {i}", i + 1
    return nome


def dax_ref(tabela, campo, tipo):
    t = "'" + tabela.replace("'", "''") + "'"
    return f"[{campo}]" if tipo == "Measure" else f"{t}[{campo}]"


# =========================================================================== medidas geradas
def medida_cor_destaque(regra, medida, categoria, tabelas, resolver):
    """Gera (tabela, nome, expressão) de uma medida que devolve a cor de cada ponto."""
    tm, ttab, tcampo = resolver(medida)
    if tm != "Measure":
        raise ErroRecurso("destaque precisa de uma medida no eixo de valores")
    mref = f"[{tcampo}]"
    if "top" in regra:
        if not categoria:
            raise ErroRecurso("destaque.top precisa de um campo de categoria")
        _, ct, cc = categoria
        n = int(regra["top"])
        expr = (f"VAR _posicao = RANKX(ALLSELECTED({dax_ref(ct, cc, 'Column')}), {mref}, , DESC)\n"
                f"RETURN IF(_posicao <= {n}, \"{regra.get('cor', DESTAQUE)}\", \"{NEUTRO}\")")
        sufixo = f"top {n}"
    elif "abaixo_de" in regra or "acima_de" in regra:
        chave = "abaixo_de" if "abaixo_de" in regra else "acima_de"
        rt, rtab, rcampo = resolver(regra[chave])
        ref = dax_ref(rtab, rcampo, rt)
        op = "<" if chave == "abaixo_de" else ">"
        expr = (f"IF({mref} {op} {ref}, \"{regra.get('cor', ALERTA)}\", \"{NEUTRO}\")")
        sufixo = f"{'abaixo' if op == '<' else 'acima'} de {rcampo}"
    elif "categoria" in regra:
        if not categoria:
            raise ErroRecurso("destaque.categoria precisa de um campo de categoria")
        _, ct, cc = categoria
        valor = str(regra["categoria"]).replace('"', '""')
        expr = (f"IF(SELECTEDVALUE({dax_ref(ct, cc, 'Column')}) = \"{valor}\", "
                f"\"{regra.get('cor', DESTAQUE)}\", \"{NEUTRO}\")")
        sufixo = regra["categoria"]
    else:
        raise ErroRecurso("destaque aceita: top, abaixo_de, acima_de, categoria ou medida_cor")
    return ttab, nome_unico(f"Cor {tcampo} ({sufixo})", tabelas), expr


def medida_titulo(cfg, tabelas, resolver):
    mt, mtab, mcampo = resolver(cfg["medida"])
    rotulo = cfg.get("texto", mcampo).replace('"', '""')
    fmt = cfg.get("formato", "#,0")
    linhas = [f"VAR _valor = [{mcampo}]"]
    if cfg.get("meta"):
        rt, rtab, rcampo = resolver(cfg["meta"])
        linhas += [f"VAR _meta = {dax_ref(rtab, rcampo, rt)}",
                   "VAR _pct = DIVIDE(_valor, _meta)",
                   f"RETURN \"{rotulo}: \" & FORMAT(_valor, \"{fmt}\") & "
                   "IF(ISBLANK(_meta), \"\", \" (\" & FORMAT(_pct, \"0%\") & \" da meta)\")"]
    else:
        linhas.append(f"RETURN \"{rotulo}: \" & FORMAT(_valor, \"{fmt}\")")
    return mtab, nome_unico(f"Título {mcampo}", tabelas), "\n".join(linhas)


def medida_pareto(medida, categoria, tabelas, resolver):
    _, mtab, mcampo = resolver(medida)
    _, ct, cc = categoria
    col = dax_ref(ct, cc, "Column")
    expr = (f"VAR _atual = [{mcampo}]\n"
            f"VAR _total = CALCULATE([{mcampo}], ALLSELECTED({col}))\n"
            f"VAR _acumulado = SUMX(FILTER(ALLSELECTED({col}), CALCULATE([{mcampo}]) >= _atual), CALCULATE([{mcampo}]))\n"
            "RETURN DIVIDE(_acumulado, _total)")
    return mtab, nome_unico(f"{mcampo} % acumulado por {cc}", tabelas), expr


# =========================================================================== pseudotipos
PSEUDOTIPOS = {"dispersao": "scatterChart", "real_meta": "lineClusteredColumnComboChart", "combo": "lineClusteredColumnComboChart",
               "slope": "lineChart", "slopegraph": "lineChart", "mapa_calor": "pivotTable", "pareto": "lineClusteredColumnComboChart",
               "botao": "actionButton", "navegador": "pageNavigator"}


def expandir(spec, tabelas, resolver, criar_medida):
    """Converte pseudotipos em visuais reais. Pode criar medidas (via criar_medida)."""
    tipo = spec["tipo"]
    s = dict(spec)
    campos = dict(s.get("campos", {}))
    if tipo in ("real_meta",):
        # {"Category": dim, "Y": realizado, "Meta": meta}
        s["tipo"] = "lineClusteredColumnComboChart"
        s["campos"] = {"Category": campos["Category"], "ColumnY": campos.get("Y") or campos.get("ColumnY"),
                       "Y": campos["Meta"]}
        s.setdefault("eixo_unico", True)
        s.setdefault("so_marcadores", True)
        s.setdefault("ordenar", "desc")
        if "destaque" not in s:
            s["destaque"] = {"abaixo_de": campos["Meta"]}
    elif tipo == "pareto":
        cat = resolver(campos["Category"])
        y = campos["Y"] if isinstance(campos["Y"], str) else campos["Y"][0]
        tab, nome, expr = medida_pareto(y, cat, tabelas, resolver)
        criar_medida(tab, nome, expr, "0%", "Storytelling\\Pareto",
                     f"Percentual acumulado de {y} por {cat[2]} (curva de Pareto).")
        s["tipo"] = "lineClusteredColumnComboChart"
        s["campos"] = {"Category": campos["Category"], "ColumnY": y, "Y": f"{tab}[{nome}]"}
        s.setdefault("ordenar", "desc")
    elif tipo in ("slope", "slopegraph"):
        if "valores" not in s or len(s["valores"]) != 2:
            raise ErroRecurso("slope precisa de 'valores' com os dois períodos a comparar (ex.: [2025, 2026])")
        s["tipo"] = "lineChart"
        s["filtro_categoria"] = {"campo": campos["Category"], "valores": s["valores"]}
        s.setdefault("rotulos", True)
        s.setdefault("grade", False)
    elif tipo == "mapa_calor":
        s["tipo"] = "pivotTable"
        s.setdefault("gradiente", True)
    elif tipo in PSEUDOTIPOS:
        s["tipo"] = PSEUDOTIPOS[tipo]
    return s


# =========================================================================== opções de formatação
def _objs(visual):
    return visual.setdefault("objects", {})


def _vco(visual):
    return visual.setdefault("visualContainerObjects", {})


def aplicar_opcoes(v, spec, tabelas, resolver, criar_medida, paginas_por_nome=None, ordem_padrao=True):
    """Aplica opções de Storytelling/UX num visual.json (dict completo). Retorna lista de avisos."""
    avisos = []
    visual = v["visual"]
    tipo = visual.get("visualType")
    estado = visual.get("query", {}).get("queryState", {})

    def primeiro(papel):
        for p in estado.get(papel, {}).get("projections", []):
            f = p["field"]
            k = "Measure" if "Measure" in f else ("Column" if "Column" in f else None)
            if k:
                return k, f[k]["Expression"]["SourceRef"]["Entity"], f[k]["Property"], p["queryRef"]
        return None

    cat = primeiro("Category") or primeiro("Rows")
    val = primeiro("ColumnY") or primeiro("Y") or primeiro("Values")

    # ordenação
    ordem = spec.get("ordenar")
    if ordem is None and ordem_padrao and tipo in ("clusteredBarChart", "clusteredColumnChart") and cat and val:
        eh_tempo = re.search(r"(data|date|ano|mes|competencia|periodo|semana|dia|trimestre|year|month)",
                             cat[2].lower())
        ordem = "asc_categoria" if eh_tempo else "desc"
    if ordem and ordem != "nenhuma":
        alvo = cat if ordem == "asc_categoria" else val
        if alvo:
            direcao = "Ascending" if ordem in ("asc", "asc_categoria") else "Descending"
            visual.setdefault("query", {})["sortDefinition"] = {
                "sort": [{"field": campo_expr(alvo[0], alvo[1], alvo[2]), "direction": direcao}],
                "isDefaultSort": False}

    if spec.get("modo") and tipo in ("slicer",) and spec.get("_formatar"):
        dados = _objs(visual).setdefault("data", [{"properties": {}}])[0].setdefault("properties", {})
        dados["mode"] = texto(spec["modo"])
    if spec.get("legenda") is False:
        _objs(visual)["legend"] = [{"properties": {"show": lit("false")}}]
    elif spec.get("legenda") is True:
        _objs(visual)["legend"] = [{"properties": {"show": lit("true"), "position": texto("Top")}}]
    if spec.get("grade") is False:
        _objs(visual)["valueAxis"] = [{"properties": {"gridlineShow": lit("false")}}]
    if spec.get("rotulos") is not None:
        _objs(visual)["labels"] = [{"properties": {"show": lit("true" if spec["rotulos"] else "false"),
                                                   "labelDisplayUnits": num(1)}}]
    if spec.get("eixo_unico"):
        va = _objs(visual).setdefault("valueAxis", [{"properties": {}}])[0]["properties"]
        va["secShow"] = lit("false")
        avisos.append("eixo único (secShow=false): confira no Desktop se realizado e meta ficaram na mesma escala")
    if spec.get("so_marcadores"):
        _objs(visual)["lineStyles"] = [{"properties": {"showMarker": lit("true"), "strokeWidth": num(0),
                                                       "markerSize": num(8)}}]

    # destaque: cor por medida (base neutra + cor de destaque)
    d = spec.get("destaque")
    if d:
        if "medida_cor" in d:
            ct, ctab, ccampo = resolver(d["medida_cor"])
        else:
            if not val:
                raise ErroRecurso("destaque precisa de uma medida no visual")
            tab, nome, expr = medida_cor_destaque(d, f"{val[1]}[{val[2]}]",
                                                  (cat[0], cat[1], cat[2]) if cat else None, tabelas, resolver)
            criar_medida(tab, nome, expr, None, "Storytelling\\Cores",
                         "Cor de destaque (Storytelling com Dados: base neutra + uma cor para o que importa).")
            ctab, ccampo = tab, nome
        _objs(visual)["dataPoint"] = [{
            "properties": {"fill": {"solid": {"color": {"expr": campo_expr("Measure", ctab, ccampo)}}}},
            "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": val[3]}}]

    # linha de referência (meta/média) no eixo de valores
    lm = spec.get("linha_meta")
    if lm:
        if isinstance(lm, (int, float)):
            valor = num(lm)
        else:
            mt, mtab, mcampo = resolver(lm)
            valor = {"expr": campo_expr(mt, mtab, mcampo)}
        _objs(visual)["y1AxisReferenceLine"] = [{
            "properties": {"show": lit("true"), "displayName": texto(spec.get("rotulo_meta", "Meta")),
                           "value": valor, "lineColor": cor(TEXTO_SECUNDARIO), "style": texto("dashed"),
                           "dataLabelShow": lit("true")},
            "selector": {"id": "1"}}]
        avisos.append("linha de meta (y1AxisReferenceLine): confira no painel Análise do Desktop")

    # mapa de calor: gradiente no(s) valor(es)
    if spec.get("gradiente"):
        regras = []
        for p in estado.get("Values", {}).get("projections", []):
            f = p["field"]
            if "Measure" not in f and "Aggregation" not in f:
                continue
            regras.append({
                "properties": {"backColor": {"solid": {"color": {"expr": {"FillRule": {
                    "Input": f,
                    "FillRule": {"linearGradient2": {
                        "min": {"color": {"Literal": {"Value": "'#F3F6FA'"}}},
                        "max": {"color": {"Literal": {"Value": f"'{DESTAQUE}'"}}},
                        "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}}}}}}}}}},
                "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": p["queryRef"]}})
        if regras:
            _objs(visual)["values"] = regras

    # filtro do visual (slopegraph: só dois períodos)
    fc = spec.get("filtro_categoria")
    if fc:
        ft, ftab, fcampo = resolver(fc["campo"])
        tipo_col = (tabelas.get(ftab, {}).get("colunas") or {})
        tipo_col = tipo_col.get(fcampo) if isinstance(tipo_col, dict) else None
        v.setdefault("filterConfig", {"filters": []})["filters"].append({
            "name": novo_nome(), "field": campo_expr("Column", ftab, fcampo), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "f", "Entity": ftab, "Type": 0}],
                       "Where": [{"Condition": {"In": {
                           "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": fcampo}}],
                           "Values": [[valor_literal(x, tipo_col)] for x in fc["valores"]]}}}]},
            "howCreated": "User"})

    # títulos e textos
    vco = _vco(visual)
    tm = spec.get("titulo_medida")
    td = spec.get("titulo_dinamico")
    if td:
        tab, nome, expr = medida_titulo(td, tabelas, resolver)
        criar_medida(tab, nome, expr, None, "Storytelling\\Títulos",
                     "Título dinâmico: mantém a frase verdadeira quando os filtros mudam.")
        tm = f"{tab}[{nome}]"
    if tm:
        mt, mtab, mcampo = resolver(tm)
        props = vco.setdefault("title", [{"properties": {}}])[0].setdefault("properties", {})
        props["text"] = {"expr": campo_expr("Measure", mtab, mcampo)}
        props["show"] = lit("true")
    if spec.get("subtitulo"):
        vco["subTitle"] = [{"properties": {"show": lit("true"), "text": texto(spec["subtitulo"]),
                                           "fontColor": cor(TEXTO_SECUNDARIO), "fontSize": num(10)}}]
    alt = spec.get("texto_alt") or spec.get("titulo")
    if alt and tipo not in ("textbox", "shape", "image"):
        vco.setdefault("general", [{"properties": {}}])[0].setdefault("properties", {})["altText"] = texto(alt)

    # dica de ferramenta de página
    tp = spec.get("tooltip_pagina")
    if tp:
        pid = (paginas_por_nome or {}).get(tp, tp)
        vco["visualTooltip"] = [{"properties": {"show": lit("true"), "type": texto("Canvas"), "section": texto(pid)}}]
    return avisos


# =========================================================================== botões e navegação
ACOES = {"voltar": "Back", "pagina": "PageNavigation", "drillthrough": "Drillthrough",
         "limpar_filtros": "ClearAllSlicers", "bookmark": "Bookmark", "url": "WebUrl"}


def montar_botao(spec, paginas_por_nome):
    acao = spec.get("acao", "pagina")
    if acao not in ACOES:
        raise ErroRecurso(f"Ação de botão '{acao}' inválida. Use: {', '.join(ACOES)}")
    rotulo = spec.get("texto") or {"voltar": "← Voltar", "limpar_filtros": "Limpar filtros"}.get(acao, "Abrir")
    link = {"show": lit("true"), "type": texto(ACOES[acao])}
    if acao in ("pagina", "drillthrough"):
        destino = spec.get("destino")
        if not destino:
            raise ErroRecurso("Botão de página/drill-through precisa de 'destino' (id ou nome da página)")
        pid = paginas_por_nome.get(destino, destino)
        link["navigationSection" if acao == "pagina" else "drillthroughSection"] = texto(pid)
    if acao == "url":
        link["webUrl"] = texto(spec["destino"])
    visual = {"visualType": "actionButton",
              "objects": {"icon": [{"properties": {"shapeType": texto("back" if acao == "voltar" else "blank")},
                                    "selector": {"id": "default"}}],
                          "text": [{"properties": {"show": lit("true"), "text": texto(rotulo),
                                                   "fontColor": cor("#163B65"), "fontSize": num(11)},
                                    "selector": {"id": "default"}}],
                          "fill": [{"properties": {"show": lit("true"), "fillColor": cor("#FFFFFF")},
                                    "selector": {"id": "default"}}]},
              "visualContainerObjects": {"visualLink": [{"properties": link}],
                                         "general": [{"properties": {"altText": texto(rotulo)}}]},
              "drillFilterOtherVisuals": True}
    return visual


def montar_navegador():
    return {"visualType": "pageNavigator",
            "visualContainerObjects": {"general": [{"properties": {"altText": texto("Navegação entre páginas")}}]},
            "drillFilterOtherVisuals": True}


# =========================================================================== páginas especiais
def configurar_pagina_especial(pagina, pspec, resolver):
    tipo = (pspec.get("tipo") or "").lower()
    if tipo in ("drillthrough", "drill-through", "detalhe"):
        ref = pspec.get("campo_drill")
        if not ref:
            raise ErroRecurso("Página de drill-through precisa de 'campo_drill' (ex.: DimTurma[TurmaID])")
        t, tab, campo = resolver(ref)
        filtro = novo_nome()
        expr = campo_expr(t, tab, campo)
        pagina["type"] = "Drillthrough"
        pagina["visibility"] = "HiddenInViewMode"
        pagina["pageBinding"] = {"name": novo_nome(), "type": "Drillthrough",
                                 "parameters": [{"name": novo_nome(), "boundFilter": filtro, "fieldExpr": expr}]}
        pagina["filterConfig"] = {"filters": [{"name": filtro, "field": expr, "type": "Categorical",
                                               "howCreated": "Drillthrough"}]}
        return "drillthrough"
    if tipo in ("tooltip", "dica"):
        pagina["type"] = "Tooltip"
        pagina["visibility"] = "HiddenInViewMode"
        pagina["pageBinding"] = {"name": novo_nome(), "type": "Tooltip"}
        pagina["width"] = pspec.get("largura", 320)
        pagina["height"] = pspec.get("altura", 240)
        pagina["displayOption"] = "FitToPage"
        return "tooltip"
    if pspec.get("oculta"):
        pagina["visibility"] = "HiddenInViewMode"
    return None


# =========================================================================== alinhamento e layout
def _agrupar(valores, tol):
    """Mapa valor → valor canônico (moda do grupo; empate = menor)."""
    vs = sorted(valores)
    grupos, atual = [], [vs[0]] if vs else []
    for x in vs[1:]:
        if x - atual[-1] <= tol:
            atual.append(x)
        else:
            grupos.append(atual)
            atual = [x]
    if atual:
        grupos.append(atual)
    mapa = {}
    for g in grupos:
        canon = sorted(Counter(g).items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        for x in g:
            mapa[x] = canon
    return mapa


def _sobrepoe(a, b):
    ox = min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"])
    oy = min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"])
    return ox > 4 and oy > 4


def alinhar(visuais, largura, altura, tol=8):
    """visuais: lista de dicts visual.json. Ajusta posições in-place. Retorna nº de visuais alterados."""
    pos = [v["position"] for v in visuais if "position" in v]
    if len(pos) < 2:
        return 0
    antes = [dict(p) for p in pos]
    for eixo, tam in (("x", "width"), ("y", "height")):
        inicio = _agrupar([round(p[eixo]) for p in pos], tol)
        fim = _agrupar([round(p[eixo] + p[tam]) for p in pos], tol)
        for p in pos:
            a, b = inicio[round(p[eixo])], fim[round(p[eixo] + p[tam])]
            if b - a >= 20:
                p[eixo], p[tam] = a, b - a
    # desfaz o que criou sobreposição ou saiu da página
    for i, p in enumerate(pos):
        fora = p["x"] < 0 or p["y"] < 0 or p["x"] + p["width"] > largura or p["y"] + p["height"] > altura
        novo_conflito = any(_sobrepoe(p, q) and not _sobrepoe(antes[i], antes[j])
                            for j, q in enumerate(pos) if j != i)
        if fora or novo_conflito:
            p.update(antes[i])
    return sum(1 for a, p in zip(antes, pos) if a != p)


# =========================================================================== troca de tipo
FAMILIA_CATEGORIA = {"clusteredBarChart", "clusteredColumnChart", "lineChart", "barChart", "columnChart",
                     "stackedBarChart", "areaChart", "pieChart", "donutChart", "hundredPercentStackedBarChart",
                     "hundredPercentStackedColumnChart", "lineClusteredColumnComboChart", "funnel", "treemap"}
MAPA_PAPEIS = {"Legend": "Series", "Values": "Y", "ColumnY": "Y", "Details": "Category", "Group": "Category"}
PAPEIS_DESTINO = {"clusteredBarChart": {"Category", "Y", "Series", "Tooltips"},
                  "clusteredColumnChart": {"Category", "Y", "Series", "Tooltips"},
                  "lineChart": {"Category", "Y", "Series", "Tooltips"},
                  "card": {"Values"}, "tableEx": {"Values"},
                  "donutChart": {"Category", "Y", "Tooltips"}}


def trocar_tipo(v, novo):
    visual = v["visual"]
    antigo = visual.get("visualType")
    if novo not in PAPEIS_DESTINO:
        raise ErroRecurso(f"Destino '{novo}' não suportado. Use: {', '.join(PAPEIS_DESTINO)}")
    estado = visual.get("query", {}).get("queryState", {})
    novo_estado = {}
    descartados = []
    for papel, bloco in estado.items():
        destino = papel
        if novo == "card":
            destino = "Values" if papel in ("Y", "Values", "ColumnY") else None
        elif novo == "tableEx":
            destino = "Values"
        else:
            destino = MAPA_PAPEIS.get(papel, papel)
            if antigo == "gauge" and papel in ("MinValue", "MaxValue", "TargetValue"):
                destino = "Tooltips"
        if destino not in PAPEIS_DESTINO[novo]:
            descartados.append(papel)
            continue
        novo_estado.setdefault(destino, {"projections": []})["projections"] += bloco.get("projections", [])
    if novo == "card" and len(novo_estado.get("Values", {}).get("projections", [])) > 1:
        novo_estado["Values"]["projections"] = novo_estado["Values"]["projections"][:1]
    visual["visualType"] = novo
    visual["query"] = {"queryState": novo_estado}
    manter = {k: visual.get("objects", {})[k] for k in ("labels",) if k in visual.get("objects", {})}
    visual["objects"] = manter
    if not manter:
        visual.pop("objects")
    return antigo, descartados


# =========================================================================== tema corporativo
def tema_padrao(nome="Tema Storytelling", destaque=DESTAQUE, titulo="#163B65", fundo_pagina="#F3F6FA"):
    return {
        "name": nome,
        "dataColors": [destaque, "#163B65", ALERTA, "#5A6B7B", "#7FB2E5", "#A5ADB7", "#3C8DBC", "#8C6D46"],
        "foreground": "#252423", "foregroundNeutralSecondary": TEXTO_SECUNDARIO,
        "background": "#FFFFFF", "backgroundLight": fundo_pagina, "backgroundNeutral": NEUTRO,
        "tableAccent": destaque, "good": destaque, "neutral": NEUTRO, "bad": ALERTA,
        "maximum": destaque, "center": "#9CC3E6", "minimum": fundo_pagina, "null": "#FFFFFF",
        "textClasses": {
            "title": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": titulo},
            "header": {"fontFace": "Segoe UI Semibold", "fontSize": 14, "color": titulo},
            "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": "#252423"},
            "callout": {"fontFace": "Segoe UI", "fontSize": 27, "color": destaque},
        },
        "visualStyles": {
            "*": {"*": {
                "border": [{"show": False}],
                "dropShadow": [{"show": False}],
                "background": [{"show": True, "color": {"solid": {"color": "#FFFFFF"}}, "transparency": 0}],
                "title": [{"show": True, "fontColor": {"solid": {"color": titulo}}, "fontSize": 12, "titleWrap": True}],
                "padding": [{"top": 12, "bottom": 12, "left": 16, "right": 16}],
                "valueAxis": [{"gridlineShow": False}],
            }},
            "page": {"*": {"background": [{"color": {"solid": {"color": fundo_pagina}}, "transparency": 0}]}},
        },
    }


def aplicar_tema(report: Path, tema: dict, simular=False):
    defin = report / "definition"
    rj = defin / "report.json"
    rep = json.loads(rj.read_text(encoding="utf-8-sig"))
    arquivo = re.sub(r"[^A-Za-z0-9_-]+", "_", tema.get("name", "Tema")) + ".json"
    destino = report / "StaticResources" / "RegisteredResources" / arquivo
    base = rep.setdefault("themeCollection", {}).get("baseTheme", {})
    rep["themeCollection"]["customTheme"] = {
        "name": arquivo,
        "reportVersionAtImport": base.get("reportVersionAtImport", {"visual": "2.6.0", "report": "3.1.0", "page": "2.3.0"}),
        "type": "RegisteredResources"}
    pacotes = rep.setdefault("resourcePackages", [])
    reg = next((p for p in pacotes if p.get("type") == "RegisteredResources"), None)
    if reg is None:
        reg = {"name": "RegisteredResources", "type": "RegisteredResources", "items": []}
        pacotes.append(reg)
    reg["items"] = [i for i in reg["items"] if i.get("type") != "CustomTheme"] + \
                   [{"name": arquivo, "path": arquivo, "type": "CustomTheme"}]
    if not simular:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(tema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rj.write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destino
