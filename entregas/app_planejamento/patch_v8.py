"""Desenvolvimento_8 = Desenvolvimento_7 + status automático, filtro de execução/delegação,
calendário multimodalidade e desconto de almoço no turno Integral.
Uso: python3 -I patch_v8.py <entrada_v7.msapp> <saida_v8.msapp>
Edita Controls/*.json (o que o Studio carrega). Os Src/*.pa.yaml são regenerados pelo Studio ao salvar."""
import json, re, sys, zipfile

SRC, DST = sys.argv[1], sys.argv[2]

# ---------------------------------------------------------------- utilidades
def walk(n):
    yield n
    for c in n.get('Children', []):
        yield from walk(c)

class Screen:
    def __init__(self, d):
        self.d = d
        self.nodes = {n['Name']: n for n in walk(d['TopParent'])}

    def rule(self, ctrl, prop):
        rs = [r for r in self.nodes[ctrl]['Rules'] if r['Property'] == prop]
        assert len(rs) == 1, (ctrl, prop, len(rs))
        return rs[0]

    def set(self, ctrl, prop, value, expect=None):
        r = self.rule(ctrl, prop)
        if expect is not None:
            assert r['InvariantScript'].strip() == expect.strip(), (ctrl, prop, r['InvariantScript'])
        r['InvariantScript'] = value

    def sub(self, ctrl, prop, pattern, repl, count=1):
        r = self.rule(ctrl, prop)
        new, n = re.subn(pattern, repl, r['InvariantScript'], flags=re.S)
        assert n == count, (ctrl, prop, pattern[:60], n)
        r['InvariantScript'] = new

    def sub_all_rules(self, pattern, repl):
        total = 0
        for n in walk(self.d['TopParent']):
            for r in n['Rules']:
                new, k = re.subn(pattern, repl, r['InvariantScript'], flags=re.S)
                if k:
                    r['InvariantScript'] = new
                    total += k
        return total

    def find_label(self, parent, text):
        hits = [c for c in walk(self.nodes[parent])
                if any(r['Property'] == 'Text' and r['InvariantScript'].strip() == text for r in c['Rules'])]
        assert len(hits) == 1, (parent, text, len(hits))
        return hits[0]['Name']


# ---------------------------------------------------------------- 1. STATUS
STATUS_CALC_SALVAR = '''Status_Turma:
                                        With(
                                            {
                                                _manual:
                                                    If(
                                                        varModoFormulario = "Novo",
                                                        {Value: "Rascunho"},
                                                        DataCardValue34.Selected
                                                    ),
                                                _inicio: dteInicioPrevisto.SelectedDate,
                                                _fim: dteFimPrevisto.SelectedDate
                                            },
                                            If(
                                                _manual.Value = "Cancelada",
                                                _manual,
                                                !IsBlank(_fim) && Today() > _fim,
                                                {Value: "Concluída"},
                                                !IsBlank(_inicio) && Today() >= _inicio,
                                                {Value: "Em execução"},
                                                _manual.Value = "Em execução" ||
                                                _manual.Value = "Concluída",
                                                {Value: "Planejada"},
                                                _manual
                                            )
                                        ),'''

STATUS_CALC_GALERIA = '''_status:
            With(
                {
                    _statusGravado:
                        Coalesce(
                            ThisItem.Status_Turma.Value,
                            "Rascunho"
                        )
                },
                If(
                    _statusGravado = "Cancelada",
                    _statusGravado,
                    !IsBlank(ThisItem.Data_Fim_Prevista) &&
                    Today() > ThisItem.Data_Fim_Prevista,
                    "Concluída",
                    !IsBlank(ThisItem.Data_Inicio_Prevista) &&
                    Today() >= ThisItem.Data_Inicio_Prevista,
                    "Em execução",
                    _statusGravado = "Em execução" ||
                    _statusGravado = "Concluída",
                    "Planejada",
                    _statusGravado
                )
            ),'''


def patch_cadastro_turma(s):
    s.sub('btnSalvarTurma', 'OnSelect',
          r'Status_Turma:\s*If\(\s*varModoFormulario = "Novo",\s*\{Value: "Rascunho"\},\s*DataCardValue34\.Selected\s*\),',
          STATUS_CALC_SALVAR.replace('\\', '\\\\'))
    s.set('DataCardKey53', 'Text',
          '"Situação da turma (Em execução e Concluída são definidas pelas datas)"',
          expect='"Situação da turma"')


# ---------------------------------------------------------------- 2. FILTRO
GAL_EXEC_CASE = '''"Período de execução",
                            (
                                IsBlank(f.DataAte) ||
                                t.Data_Inicio_Prevista < DateAdd(f.DataAte, 1, TimeUnit.Days)
                            ) &&
                            (
                                IsBlank(f.DataDe) ||
                                t.Data_Fim_Prevista >= f.DataDe
                            ),

                            "Período de fim",'''


def patch_turmas(s):
    # filtro delegável primeiro (unidade + ativa), filtros locais depois
    s.sub('Gallery1', 'Items',
          r'Filter\(\s*Turmas_Planejadas As t,\s*t\.Ativa = true &&\s*t\.Unidade\.Id = varPlanejamentoSelecionado\.Unidade\.Id &&\s*IsEmpty\(',
          'Filter(\n        Filter(\n            Turmas_Planejadas,\n            Ativa = true &&\n'
          '            Unidade.Id = varPlanejamentoSelecionado.Unidade.Id\n        ) As t,\n\n        IsEmpty(')
    s.sub('Gallery1', 'Items', r'"Período de fim",', GAL_EXEC_CASE)
    s.sub('Gallery1', 'Items', r'"Situação",\s*StartsWith\(t\.Status_Turma\.Value, f\.Valor\)',
          '"Situação",\n                            StartsWith(t.Status_Turma.Value, f.Valor)')
    # nova opção no combo
    s.sub('cmbCampoBuscaTurma', 'Items', r'\{Campo: "Período de fim"\}',
          '{Campo: "Período de fim"},\n    {Campo: "Período de execução"}')
    # todas as condições "início || fim" passam a incluir "execução"
    n = s.sub_all_rules(
        r'([\w.]+) = "Período de início" \|\|(\s+)\1 = "Período de fim"(?! \|\|\s+[\w.]+ = "Período de execução")',
        r'\1 = "Período de início" ||\2\1 = "Período de fim" ||\2\1 = "Período de execução"')
    assert n >= 6, n
    s.set('Label11', 'Text',
          'Switch(\n    cmbCampoBuscaTurma.Selected.Campo,\n'
          '    "Período de execução",\n    "*Turmas em execução em algum dia do intervalo",\n'
          '    "*Turmas com início no intervalo acima"\n)',
          expect='"*Turmas com início no intervalo acima"')
    s.set('Label11', 'Visible',
          'cmbCampoBuscaTurma.Selected.Campo = "Período de início" ||\n'
          'cmbCampoBuscaTurma.Selected.Campo = "Período de execução"',
          expect='cmbCampoBuscaTurma.Selected.Campo = "Período de início"')


# ---------------------------------------------------------------- 3. CALENDÁRIO
CAL_PATCH_OLD = r'IfError\(\s*Patch\(\s*Cad_Calendario,.*?Ativo:\s*DataCardValue32\.Value\s*\}\s*\),'
CAL_PATCH_NEW = '''IfError(
        With(
            {
                _modalidades: DataCardValue25.SelectedItems,
                _dados: {
                    Unidade:
                        DataCardValue26.Selected,

                    Unidade_ID:
                        DataCardValue26.Selected.Id,

                    Tipo_Dia:
                        DataCardValue30.Selected,

                    Data_unica:
                        DataCardValue27.Value,

                    Data_Evento_:
                        DataCardValue31.SelectedDate,

                    Data_Fim_Evento:
                        If(
                            DataCardValue27.Value,
                            Blank(),
                            DataCardValue28.SelectedDate
                        ),

                    Descrição:
                        Trim(DataCardValue24.Text),

                    Ativo:
                        DataCardValue32.Value
                }
            },

            Patch(
                Cad_Calendario,
                If(
                    varEventoCalendarioID = 0,
                    Defaults(Cad_Calendario),
                    LookUp(
                        Cad_Calendario,
                        ID = varEventoCalendarioID
                    )
                ),
                _dados,
                {
                    Modalidade:
                        If(
                            IsEmpty(_modalidades),
                            Blank(),
                            {Value: First(_modalidades).Value}
                        )
                }
            );

            ForAll(
                LastN(
                    _modalidades,
                    CountRows(_modalidades) - 1
                ) As m,
                Patch(
                    Cad_Calendario,
                    Defaults(Cad_Calendario),
                    _dados,
                    {Modalidade: {Value: m.Value}}
                )
            )
        ),'''


def patch_calendario(s):
    s.sub('Button8', 'OnSelect', CAL_PATCH_OLD, CAL_PATCH_NEW.replace('\\', '\\\\'))
    s.sub('Button8', 'OnSelect', r'"Calendário salvo com sucesso\."',
          '"Calendário salvo com sucesso" &\n                If(\n'
          '                    CountRows(DataCardValue25.SelectedItems) > 1,\n'
          '                    " (" & CountRows(DataCardValue25.SelectedItems) & " eventos, um por modalidade).",\n'
          '                    "."\n                )')


# ---------------------------------------------------------------- 4. ALMOÇO
ALMOCO_FORM = ('(cmbHoraFim.Selected.Minutos - cmbHoraInicio.Selected.Minutos -\n'
               '            If(\n'
               '                varTurmaSelecionada.Turno.Value = "Integral" &&\n'
               '                cmbHoraFim.Selected.Minutos - cmbHoraInicio.Selected.Minutos > 240,\n'
               '                60,\n'
               '                0\n'
               '            )\n'
               '        ) / 60')


def patch_horario(s):
    old = r'\(cmbHoraFim\.Selected\.Minutos - cmbHoraInicio\.Selected\.Minutos\) / 60'
    s.sub('Carga_Horaria_Dia_DataCard1', 'Update', old, ALMOCO_FORM)
    s.sub('DataCardValue20', 'Default', old, ALMOCO_FORM)
    s.sub('Button7', 'OnSelect',
          r'\(\s*fimMinutos\s*-\s*inicioMinutos\s*\)\s*/\s*60',
          '(\n    fimMinutos - inicioMinutos -\n    If(\n'
          '        varTurmaSelecionada.Turno.Value = "Integral" &&\n'
          '        fimMinutos - inicioMinutos > 240,\n        60,\n        0\n    )\n) / 60')
    key = s.find_label('Carga_Horaria_Dia_DataCard1', '"Carga horária do dia"')
    s.set(key, 'Text',
          'If(\n    varTurmaSelecionada.Turno.Value = "Integral",\n'
          '    "Carga horária do dia (desconta 1h de almoço)",\n    "Carga horária do dia"\n)')


SCREEN_PATCH = {
    'scrCadastroTurma': [patch_cadastro_turma],
    'scrTurmas': [patch_turmas],
    'scrCalendarioEP': [patch_calendario],
    'scrHorarioTurma': [patch_horario],
}


def patch_gallery_status(s):
    s.sub('HtmlText12', 'HtmlText',
          r'_status:\s*Coalesce\(\s*ThisItem\.Status_Turma\.Value,\s*"Rascunho"\s*\),',
          STATUS_CALC_GALERIA.replace('\\', '\\\\'))


SCREEN_PATCH['scrTurmas'].append(patch_gallery_status)

zin = zipfile.ZipFile(SRC)
done = set()
with zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED) as zout:
    for info in zin.infolist():
        data = zin.read(info.filename)
        if info.filename.startswith('Controls\\'):
            d = json.loads(data)
            name = d['TopParent']['Name']
            if name in SCREEN_PATCH:
                s = Screen(d)
                for fn in SCREEN_PATCH[name]:
                    fn(s)
                data = json.dumps(d, indent=2, ensure_ascii=False).replace('\n', '\r\n').encode('utf-8')
                done.add(name)
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = info.external_attr
        zi.create_system = info.create_system
        zout.writestr(zi, data)
assert done == set(SCREEN_PATCH), done
print('ok', DST)
