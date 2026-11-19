"""Aplica os 3 ajustes ao .msapp: Controls/*.json (fonte que o Studio carrega) e Src/*.pa.yaml (espelho).
Uso: python3 -I patch_msapp.py <entrada.msapp> <saida.msapp>
Fórmulas em sintaxe invariante (vírgula / ponto-e-vírgula), como o msapp armazena."""
import json, re, sys, zipfile

SRC, DST = sys.argv[1], sys.argv[2]

ITEMS_PERIODO = '''With(
    {
        _periodos:
            Filter(
                Cad_Periodos_Letivos,
                Unidade.Id = cmbUnidade.Selected.Id &&
                (
                    Ativo = true ||
                    (
                        varModoFormulario <> "Novo" &&
                        ID = varTurmaSelecionada.Periodo_Letivo.Id
                    )
                )
            )
    },
    SortByColumns(
        ForAll(
            GroupBy(
                _periodos,
                Periodo_Letivo,
                Registros
            ) As grupo,
            If(
                IsBlank(
                    LookUp(
                        grupo.Registros,
                        ID = varTurmaSelecionada.Periodo_Letivo.Id
                    )
                ),
                First(
                    SortByColumns(
                        grupo.Registros,
                        "ID",
                        SortOrder.Ascending
                    )
                ),
                LookUp(
                    grupo.Registros,
                    ID = varTurmaSelecionada.Periodo_Letivo.Id
                )
            )
        ),
        "Periodo_Letivo",
        SortOrder.Ascending
    )
)'''

TXT_ANO_DEFAULT = '''If(
    !IsBlank(cmbPeriodoLetivo.Selected.ID),
    Text(cmbPeriodoLetivo.Selected.Ano_Referencia, "0"),
    Text(Parent.Default, "0")
)'''

TXT_ANO_DISPLAYMODE = '''If(
    IsBlank(cmbPeriodoLetivo.Selected.ID),
    Parent.DisplayMode,
    DisplayMode.View
)'''

CARD_ANO_UPDATE = '''If(
    !IsBlank(cmbPeriodoLetivo.Selected.ID),
    cmbPeriodoLetivo.Selected.Ano_Referencia,
    Value(txtAnoReferencia.Text)
)'''

TITLE2_TEXT = '''Coalesce(
    ThisItem.Nome_Planejamento,
    "Planejamento sem nome"
)'''

SUBTITLE2_TEXT = '''With(
    {
        _qtdAtivos:
            CountRows(
                Filter(
                    Planejamentos,
                    Ativo = true &&
                    Unidade.Id = ThisItem.Unidade.Id
                )
            )
    },
    If(
        _qtdAtivos > 1,
        "⚠ " & Text(_qtdAtivos, "0") & " planejamentos ativos na unidade",
        "Planejamento único da unidade"
    )
)'''

SUBTITLE2_COLOR = '''If(
    CountRows(
        Filter(
            Planejamentos,
            Ativo = true &&
            Unidade.Id = ThisItem.Unidade.Id
        )
    ) > 1,
    ColorValue("#B45309"),
    ColorValue("#64748B")
)'''

# (arquivo json, controle, propriedade) -> (valor antigo esperado, novo)
CHANGES = {
    'scrCadastroTurma': [
        ('cmbPeriodoLetivo', 'Items', None, ITEMS_PERIODO),
        ('cmbPeriodoLetivo', 'DisplayFields', '["ComplianceAssetId"]', '["Periodo_Letivo"]'),
        ('cmbPeriodoLetivo', 'SearchFields', '["ComplianceAssetId"]', '["Periodo_Letivo"]'),
        ('cmbPeriodoLetivo', 'OnChange', 'false', 'Reset(txtAnoReferencia)'),
        ('txtAnoReferencia', 'Default', 'Parent.Default', TXT_ANO_DEFAULT),
        ('txtAnoReferencia', 'DisplayMode', 'Parent.DisplayMode', TXT_ANO_DISPLAYMODE),
        ('Ano_Referencia_DataCard1', 'Update', 'Value(txtAnoReferencia.Text)', CARD_ANO_UPDATE),
        ('DataCardKey4', 'Text', '"Ano do planejamento"', '"Ano de referência"'),
    ],
    'scrPlanejamentos': [
        ('Title2', 'Text', 'ThisItem.Codigo_Planejamento', TITLE2_TEXT),
        ('Subtitle2', 'Text', 'ThisItem.Codigo_Planejamento', SUBTITLE2_TEXT),
        ('Subtitle2', 'Color', 'RGBA(0, 0, 0, 1)', SUBTITLE2_COLOR),
    ],
}


def walk(n):
    yield n
    for c in n.get('Children', []):
        yield from walk(c)


def patch_json(raw, screen):
    d = json.loads(raw)
    assert d['TopParent']['Name'] == screen
    nodes = {n['Name']: n for n in walk(d['TopParent'])}
    for ctrl, prop, old, new in CHANGES[screen]:
        rules = [r for r in nodes[ctrl]['Rules'] if r['Property'] == prop]
        assert len(rules) == 1, (ctrl, prop)
        if old is not None:
            assert rules[0]['InvariantScript'].strip() == old, (ctrl, prop, rules[0]['InvariantScript'])
        rules[0]['InvariantScript'] = new
    out = json.dumps(d, indent=2, ensure_ascii=False).replace('\n', '\r\n').encode('utf-8')
    return out


def yaml_block(prop, value, indent):
    pad = ' ' * indent
    if '\n' not in value:
        return [f'{pad}{prop}: ={value}']
    lines = [f'{pad}{prop}: |-', f'{pad}  ={value.splitlines()[0]}']
    lines += [f'{pad}  {l}' if l else '' for l in value.splitlines()[1:]]
    return lines


def patch_yaml(text, screen):
    nl = '\r\n' if '\r\n' in text else '\n'
    L = text.split(nl)
    for ctrl, prop, _old, new in CHANGES[screen]:
        start = next(i for i, l in enumerate(L) if re.match(rf'^\s*- {re.escape(ctrl)}:$', l))
        cind = len(L[start]) - len(L[start].lstrip())
        # bloco do controle até o próximo item no mesmo nível ou acima
        end = next((i for i in range(start + 1, len(L))
                    if L[i].strip() and (len(L[i]) - len(L[i].lstrip())) <= cind), len(L))
        pi = next(i for i in range(start, end) if L[i].strip() == 'Properties:')
        pind = len(L[pi]) - len(L[pi].lstrip()) + 2
        # fim da seção Properties
        pend = next((i for i in range(pi + 1, end)
                     if L[i].strip() and (len(L[i]) - len(L[i].lstrip())) < pind), end)
        new_lines = yaml_block(prop, new, pind)
        found = None
        for i in range(pi + 1, pend):
            if re.match(rf'^ {{{pind}}}{re.escape(prop)}:', L[i]):
                found = i
                break
        if found is not None:
            j = found + 1
            while j < pend and (not L[j].strip() or (len(L[j]) - len(L[j].lstrip())) > pind):
                j += 1
            L[found:j] = new_lines
        else:
            # insere em ordem alfabética entre as propriedades
            keys = [(i, L[i].strip().split(':')[0]) for i in range(pi + 1, pend)
                    if (len(L[i]) - len(L[i].lstrip())) == pind and L[i].strip()]
            pos = next((i for i, k in keys if k > prop), pend)
            L[pos:pos] = new_lines
    return nl.join(L)


JSON_FOR = {'Controls\\56.json': 'scrCadastroTurma', 'Controls\\441.json': 'scrPlanejamentos'}
YAML_FOR = {'Src\\scrCadastroTurma.pa.yaml': 'scrCadastroTurma', 'Src\\scrPlanejamentos.pa.yaml': 'scrPlanejamentos'}

zin = zipfile.ZipFile(SRC)
with zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED) as zout:
    for info in zin.infolist():
        data = zin.read(info.filename)
        if info.filename in JSON_FOR:
            data = patch_json(data, JSON_FOR[info.filename])
        elif info.filename in YAML_FOR:
            data = patch_yaml(data.decode('utf-8'), YAML_FOR[info.filename]).encode('utf-8')
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = info.external_attr
        zi.create_system = info.create_system
        zout.writestr(zi, data)
print('ok', DST)
