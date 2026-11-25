#!/usr/bin/env python3
"""Auditoria de UX/UI de apps de tela do Power Apps (.msapp ou .zip que contenha .msapp).

Uso: analisar_app.py <arquivo.msapp|.zip> [--saida PASTA]

Lê Controls/*.json (árvore de controles e fórmulas Power Fx) e aplica heurísticas de Nielsen, WCAG 2.2 e
boas práticas do Power Apps (desempenho, delegação, tratamento de erros, nomes, tema). Gera relatorio_app.md
e analise_app.json. Os achados são heurísticos: confirme no Power Apps Studio.
"""
import argparse
import json
import re
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

NOMES_CORES = {"white": "#FFFFFF", "black": "#000000", "gray": "#808080", "grey": "#808080",
               "lightgray": "#D3D3D3", "darkgray": "#A9A9A9", "red": "#FF0000", "green": "#008000",
               "blue": "#0000FF", "navy": "#000080", "yellow": "#FFFF00", "orange": "#FFA500"}
RE_RGBA = re.compile(r"^RGBA\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)$")
RE_HEXCV = re.compile(r'^ColorValue\(\s*"(#[0-9A-Fa-f]{6})"\s*\)$')
RE_COLOR = re.compile(r"^Color\.(\w+)$")
RE_TODAS_CORES = re.compile(r'RGBA\([^)]*\)|ColorValue\("#[0-9A-Fa-f]{6,8}"\)|Color\.\w+')
NOME_PADRAO = re.compile(r"^(Button|Label|Icon|Image|Gallery|TextInput|Text|ComboBox|Rectangle|Form|DataCard|"
                         r"DatePicker|Toggle|Screen|Dropdown|Container|HtmlText|Checkbox|Radio|Slider)\d+(_\d+)?$")
INTERATIVOS = {"button", "icon", "image", "toggleSwitch", "checkbox", "radio", "combobox", "dropdown",
               "text", "datepicker", "slider"}
FUNC_NAO_DELEGAVEL = re.compile(r"\b(Len|Left|Mid|Right|Lower|Upper|Trim|Value|Text|Year|Month|Day|Find)\s*\(\s*'?([A-Za-z_][\w ]*?)'?\s*[.,)]")
IN_TEXTO = re.compile(r'"[^"]*"\s+in\s+[A-Za-z_]\w*')
RAIZES_LOCAIS = ("var", "loc", "gbl", "col", "_")
RAIZES_FIXAS = {"Self", "Parent", "ThisItem", "ThisRecord", "User", "Today", "Now", "App", "Param"}


def nao_delegavel(predicado, controles):
    for m in FUNC_NAO_DELEGAVEL.finditer(predicado):
        raiz = m.group(2).strip().split(".")[0]
        if raiz in controles or raiz in RAIZES_FIXAS or raiz.startswith(RAIZES_LOCAIS):
            continue
        return f"{m.group(1)}({raiz})"
    if IN_TEXTO.search(predicado):
        return "\"texto\" in coluna"
    return None


def retangulo(r):
    vals = [numero(r.get(k)) for k in ("X", "Y", "Width", "Height")]
    return None if any(v is None for v in vals) else vals


def fundo_sob(c, anc, r):
    """Cor de fundo efetiva: Fill próprio opaco; senão forma irmã (ou de ancestral) por baixo; senão ancestral."""
    proprio = r.get("Fill")
    if proprio is not None:
        f = cor(proprio)
        if f is None:
            return None  # fórmula: indeterminado
        if f[1] >= 0.9:
            return f
    caixa = retangulo(r)
    for nivel, pai in enumerate(reversed(anc)):
        if caixa is None:
            return None
        cx, cy = caixa[0] + caixa[2] / 2, caixa[1] + caixa[3] / 2
        filhos = pai.get("Children", [])
        idx = next((i for i, x in enumerate(filhos) if x is c), len(filhos)) if nivel == 0 else len(filhos)
        for irmao in reversed(filhos[:idx]):
            ri = regras(irmao)
            if irmao["Template"]["Name"] in ("rectangle", "groupContainer", "button", "image") or "Fill" in ri:
                b = retangulo(ri)
                f = cor(ri.get("Fill", ""))
                if b is None and irmao["Template"]["Name"] in ("rectangle", "groupContainer"):
                    return None  # forma com posição em fórmula: fundo indeterminado
                if b and b[0] <= cx <= b[0] + b[2] and b[1] <= cy <= b[1] + b[3]:
                    return f if f and f[1] >= 0.9 else None
        rp = regras(pai)
        if rp.get("BackgroundImage", "").strip() not in ("", '""', "SampleImage"):
            return None  # imagem de fundo: indeterminado
        f = cor(rp.get("Fill", ""))
        if f and f[1] >= 0.9:
            return f
    return None


def cor(expr):
    e = (expr or "").strip()
    m = RE_RGBA.match(e)
    if m:
        r, g, b, a = int(m[1]), int(m[2]), int(m[3]), float(m[4])
        return (f"#{r:02X}{g:02X}{b:02X}", a)
    m = RE_HEXCV.match(e)
    if m:
        return (m[1].upper(), 1.0)
    m = RE_COLOR.match(e)
    if m:
        if m[1].lower() == "transparent":
            return ("#FFFFFF", 0.0)
        if m[1].lower() in NOMES_CORES:
            return (NOMES_CORES[m[1].lower()], 1.0)
    return None


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(a, b):
    x, y = sorted([lum(a), lum(b)], reverse=True)
    return (x + 0.05) / (y + 0.05)


def numero(expr):
    try:
        return float((expr or "").strip())
    except ValueError:
        return None


def carregar(caminho: Path):
    tmp = Path(tempfile.mkdtemp(prefix="app_"))
    if caminho.suffix.lower() == ".zip":
        with zipfile.ZipFile(caminho) as z:
            apps = [n for n in z.namelist() if n.lower().endswith(".msapp")]
            if not apps:
                raise ValueError("ZIP sem arquivo .msapp")
            z.extract(apps[0], tmp)
            caminho = tmp / apps[0]
    destino = tmp / "msapp"
    with zipfile.ZipFile(caminho) as z:
        for n in z.namelist():
            if not (destino / n).resolve().is_relative_to(destino.resolve()):
                raise ValueError(f"Caminho suspeito no .msapp: {n}")
        z.extractall(destino)
    telas = []
    app_info = None
    for f in sorted((destino / "Controls").glob("*.json")):
        top = json.loads(f.read_text(encoding="utf-8-sig"))["TopParent"]
        if top["Template"]["Name"] == "appinfo":
            app_info = top
        else:
            telas.append(top)
    fontes = []
    ds = destino / "References" / "DataSources.json"
    if ds.exists():
        fontes = [d.get("Name") for d in json.loads(ds.read_text(encoding="utf-8-sig")).get("DataSources", [])]
    return caminho.stem, telas, app_info, fontes


def regras(c):
    return {r["Property"]: r.get("InvariantScript", "") for r in c.get("Rules", [])}


def percorrer(c, ancestrais=()):
    yield c, ancestrais
    for ch in c.get("Children", []):
        yield from percorrer(ch, ancestrais + (c,))


def auditar(nome, telas, app_info, fontes):
    achados = []

    def add(cod, cat, sev, princ, titulo, evid, rec, tela=None):
        achados.append({"codigo": cod, "categoria": cat, "severidade": sev, "principio": princ, "titulo": titulo,
                        "tela": tela, "evidencia": evid, "recomendacao": rec})

    todas_formulas = []
    nomes_telas = [t["Name"] for t in telas]
    controles = {c["Name"] for t in telas for c, _ in percorrer(t)}
    navegadas = set()
    cores = Counter()
    for t in telas:
        sem_rotulo, baixo, fonte_peq, toque_peq, padrao, erro_sem_trat, delegacao = [], [], [], [], [], [], []
        literais = formulas_pos = 0
        n_controles = 0
        tem_container = False
        tem_notify = tem_patch = False
        for c, anc in percorrer(t):
            n_controles += 1
            tp = c["Template"]["Name"]
            nm = c["Name"]
            r = regras(c)
            for v in r.values():
                todas_formulas.append(v)
                cores.update(RE_TODAS_CORES.findall(v))
                for m in re.findall(r"Navigate\(\s*'?(\w+)'?", v):
                    navegadas.add(m)
            if tp in ("groupContainer", "horizontalAutoLayoutContainer", "verticalAutoLayoutContainer"):
                tem_container = True
            if NOME_PADRAO.match(nm):
                padrao.append(nm)
            # acessibilidade: controles interativos sem rótulo acessível
            clicavel = r.get("OnSelect", "false").strip() not in ("", "false", "Select(Parent)") or tp in ("icon",)
            if tp in ("icon", "image") and clicavel and not r.get("AccessibleLabel", "").strip('" '):
                sem_rotulo.append(nm)
            # contraste texto × fundo
            if tp in ("label", "button", "text") and "Color" in r:
                ct = cor(r["Color"])
                fundo = fundo_sob(c, anc, r)
                if ct and fundo and ct[1] >= 0.9:
                    k = contraste(ct[0], fundo[0])
                    tam = numero(r.get("Size")) or 13
                    if k < (3 if tam >= 18 else 4.5):
                        baixo.append(f"{nm} ({ct[0]} sobre {fundo[0]}, {k:.1f}:1)")
            tam = numero(r.get("Size"))
            if tp in ("label", "button", "text", "combobox", "datepicker") and tam is not None and tam < 11:
                fonte_peq.append(f"{nm} ({tam:g})")
            if tp in ("button", "icon", "toggleSwitch", "checkbox"):
                h, w = numero(r.get("Height")), numero(r.get("Width"))
                if (h is not None and h < 40) or (w is not None and w < 40):
                    toque_peq.append(f"{nm} ({w or '?'}×{h or '?'})")
            for prop in ("X", "Y", "Width"):
                if prop in r:
                    if numero(r[prop]) is not None:
                        literais += 1
                    else:
                        formulas_pos += 1
            for prop, f in r.items():
                if re.search(r"\b(Patch|SubmitForm|Remove|RemoveIf|UpdateIf|Collect)\s*\(", f) and \
                        prop.startswith("On") and not re.search(r"IfError|Errors\(|OnFailure|Notify\(", f):
                    erro_sem_trat.append(f"{nm}.{prop}")
                if "Notify(" in f:
                    tem_notify = True
                if re.search(r"\b(Patch|SubmitForm)\s*\(", f):
                    tem_patch = True
                for fonte in fontes:
                    padrao_ds = re.compile(r"\b(Filter|LookUp|Search|CountIf|SortByColumns|Sort)\s*\(\s*'?" +
                                           re.escape(fonte) + r"'?\s*,(.*)", re.S)
                    mm = padrao_ds.search(f)
                    motivo = nao_delegavel(mm.group(2)[:600], controles) if mm else None
                    if mm and mm.group(1) == "Search":
                        motivo = "Search"
                    if motivo:
                        delegacao.append(f"{nm}.{prop} ({fonte}: {motivo})")
        tela = t["Name"]
        if sem_rotulo:
            add("PA01", "Acessibilidade", "média", "[WCAG 1.1.1] · [Microsoft]", "Ícones/imagens clicáveis sem rótulo acessível",
                f"{len(sem_rotulo)}: {', '.join(sem_rotulo[:6])}", "Preencher AccessibleLabel com a ação (ex.: \"Voltar\").", tela)
        if baixo:
            add("PA02", "Acessibilidade", "média", "[WCAG 1.4.3] Contraste 4,5:1", "Contraste de texto insuficiente",
                "; ".join(baixo[:4]) + (f"; e mais {len(baixo) - 4}" if len(baixo) > 4 else ""),
                "Escurecer o texto ou o fundo até 4,5:1 (3:1 para texto ≥ 18 pt).", tela)
        if fonte_peq:
            add("PA03", "Acessibilidade", "baixa", "L5 Acessibilidade", "Fontes pequenas",
                ", ".join(fonte_peq[:6]), "Usar ao menos 12–13 pt em textos de leitura, sobretudo no celular.", tela)
        if toque_peq:
            add("PA04", "Acessibilidade", "baixa", "[WCAG 2.5.8] Área de toque", "Alvos de toque pequenos",
                ", ".join(toque_peq[:6]), "Manter botões/ícones com ao menos 40–44 px de altura e largura.", tela)
        if len(padrao) >= 5:
            add("PA05", "Manutenção", "baixa", "Convenção de nomes Power Apps", "Controles com nome padrão",
                f"{len(padrao)} (ex.: {', '.join(padrao[:5])})", "Renomear com prefixo e função (btnSalvar, lblTitulo, galTurmas).", tela)
        if n_controles > 150:
            add("PA06", "Desempenho", "média", "[Microsoft] Desempenho de apps", "Tela com muitos controles",
                f"{n_controles} controles.", "Dividir a tela, usar galerias/componentes e remover controles ocultos.", tela)
        if erro_sem_trat:
            add("PA07", "Feedback e erros", "média", "[Nielsen 9] · [Nielsen 1]", "Gravação sem tratamento de erro",
                ", ".join(erro_sem_trat[:5]), "Envolver Patch/SubmitForm em IfError(...) e avisar com Notify (sucesso e falha).", tela)
        if tem_patch and not tem_notify:
            add("PA08", "Feedback e erros", "baixa", "[Nielsen 1] Visibilidade do estado", "Sem confirmação ao salvar",
                "Há gravação de dados e nenhum Notify na tela.", "Mostrar Notify(\"Salvo\", NotificationType.Success).", tela)
        if delegacao:
            add("PA09", "Desempenho", "média", "[Microsoft] Delegação", "Possível consulta não delegável",
                ", ".join(delegacao[:4]),
                "Funções como in/Len/Lower/Text dentro de Filter/LookUp sobre a fonte podem limitar a 500/2000 linhas. "
                "Reescrever com operadores delegáveis ou pré-filtrar por coluna indexada.", tela)
        if literais and literais / (literais + formulas_pos) > 0.9 and not tem_container:
            add("PA10", "Layout", "baixa", "[Nielsen 4] · Responsividade", "Layout com posições fixas",
                f"{literais} posições fixas em X/Y/Width; nenhum contêiner de layout automático.",
                "Usar contêineres horizontais/verticais ou fórmulas baseadas em Parent.Width.", tela)
    # nível app
    inicio = app_info and regras(app_info).get("OnStart", "")
    if inicio and len(re.findall(r"\b(ClearCollect|Collect|Refresh)\s*\(", inicio)) > 4:
        add("PA11", "Desempenho", "média", "[Microsoft] OnStart", "OnStart carregando muitos dados",
            f"{len(re.findall(r'(ClearCollect|Collect|Refresh)', inicio))} cargas no OnStart.",
            "Mover para App.Formulas (fórmulas nomeadas), OnVisible da tela que usa, ou Concurrent().")
    orfas = [t for t in nomes_telas[1:] if t not in navegadas]
    if orfas:
        add("PA12", "Navegação", "baixa", "[Nielsen 3] Controle e liberdade", "Telas sem navegação de entrada",
            ", ".join(orfas), "Conferir se são acessíveis por algum caminho; remover as que não são usadas.")
    distintas = {c for c in cores if not c.startswith("Color.Transparent")}
    if len(distintas) > 15:
        add("PA13", "Consistência", "média", "L4 Cor consistente · [Nielsen 4]", "Cores fixas espalhadas pelo app",
            f"{len(distintas)} definições de cor diferentes nas fórmulas.",
            "Centralizar a paleta em App.Formulas (ex.: corPrimaria = ColorValue(\"#0072CE\")) e referenciar nos controles.")
    return achados


ICONE = {"alta": "🔴", "média": "🟠", "baixa": "🟡"}


def agrupar(achados):
    g = {}
    for a in achados:
        k = (a["codigo"], a["titulo"])
        if k not in g:
            g[k] = dict(a, telas=[a["tela"]] if a["tela"] else [], evid=[f"{a['tela']}: {a['evidencia']}" if a["tela"] else a["evidencia"]])
        else:
            g[k]["telas"].append(a["tela"])
            g[k]["evid"].append(f"{a['tela']}: {a['evidencia']}")
    saida = []
    for a in g.values():
        a["tela"] = ", ".join(a.pop("telas")) or None
        ev = a.pop("evid")
        a["evidencia"] = ev[0] if len(ev) == 1 else f"{len(ev)} telas. " + " | ".join(ev[:4]) + (" | …" if len(ev) > 4 else "")
        saida.append(a)
    return saida


def relatorio(nome, telas, fontes, achados):
    ordem = {"alta": 0, "média": 1, "baixa": 2}
    n = sum(1 for t in telas for _ in percorrer(t))
    L = [f"# Análise de UX do app — {nome}\n", f"{len(telas)} telas · {n} controles · fontes de dados: "
         + (", ".join(f for f in fontes if f) or "—") + "\n",
         "Referências: Nielsen, WCAG 2.2, boas práticas do Power Apps e *Storytelling com Dados* (L4/L5). "
         "Heurísticas estáticas: confirme no Power Apps Studio.\n", "## Telas\n", "| Tela | Controles |", "|---|---|"]
    for t in telas:
        L.append(f"| {t['Name']} | {sum(1 for _ in percorrer(t))} |")
    L.append("\n## Melhorias sugeridas\n")
    for i, a in enumerate(sorted(achados, key=lambda x: (ordem[x["severidade"]], x["codigo"])), 1):
        a["id"] = f"A{i:02d}"
        L.append(f"### {a['id']} {ICONE[a['severidade']]} {a['titulo']}" + (f" — {a['tela']}" if a["tela"] else ""))
        L += [f"- **Por quê:** {a['evidencia']}", f"- **O que fazer:** {a['recomendacao']}",
              f"- **Princípio:** {a['principio']} · `{a['codigo']}`\n"]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada")
    ap.add_argument("--saida")
    a = ap.parse_args()
    try:
        nome, telas, info, fontes = carregar(Path(a.entrada))
    except (ValueError, zipfile.BadZipFile, KeyError) as e:
        sys.exit(f"ERRO  {e}")
    achados = agrupar(auditar(nome, telas, info, fontes))
    saida = Path(a.saida or f"analise_app_{nome}")
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "relatorio_app.md").write_text(relatorio(nome, telas, fontes, achados), encoding="utf-8")
    (saida / "analise_app.json").write_text(json.dumps(achados, ensure_ascii=False, indent=1), encoding="utf-8")
    cont = Counter(x["severidade"] for x in achados)
    print(f"{nome}: {len(telas)} telas, {len(achados)} achados (média {cont['média']}, baixa {cont['baixa']}) "
          f"→ {saida / 'relatorio_app.md'}")


if __name__ == "__main__":
    main()
