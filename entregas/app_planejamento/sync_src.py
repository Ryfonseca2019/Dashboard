"""Espelha em Src/*.pa.yaml as regras alteradas em Controls/*.json entre dois .msapp.
Uso: python3 -I sync_src.py <base.msapp> <alterado.msapp> <saida.msapp>"""
import json, re, sys, zipfile
A, B, OUT = sys.argv[1:4]

def walk(n):
    yield n
    for c in n.get('Children', []): yield from walk(c)

def rules(d):
    return {(n['Name'], r['Property']): r['InvariantScript'] for n in walk(d['TopParent']) for r in n['Rules']}

def yaml_block(prop, value, indent):
    pad = ' ' * indent
    value = value.replace('\r\n', '\n').strip('\n')
    if '\n' not in value:
        return [f'{pad}{prop}: ={value}']
    ls = value.split('\n')
    return [f'{pad}{prop}: |-', f'{pad}  ={ls[0]}'] + [f'{pad}  {l}'.rstrip() if l.strip() else '' for l in ls[1:]]

def patch_yaml(text, changes):
    nl = '\r\n' if '\r\n' in text else '\n'
    L = text.split(nl)
    for ctrl, prop, new in changes:
        start = next(i for i, l in enumerate(L) if re.match(rf'^\s*- {re.escape(ctrl)}:$', l))
        cind = len(L[start]) - len(L[start].lstrip())
        end = next((i for i in range(start + 1, len(L)) if L[i].strip() and len(L[i]) - len(L[i].lstrip()) <= cind), len(L))
        pi = next(i for i in range(start, end) if L[i].strip() == 'Properties:')
        pind = len(L[pi]) - len(L[pi].lstrip()) + 2
        pend = next((i for i in range(pi + 1, end) if L[i].strip() and len(L[i]) - len(L[i].lstrip()) < pind), end)
        newl = yaml_block(prop, new, pind)
        found = next((i for i in range(pi + 1, pend) if re.match(rf'^ {{{pind}}}{re.escape(prop)}:', L[i])), None)
        if found is not None:
            j = found + 1
            while j < pend and (not L[j].strip() or len(L[j]) - len(L[j].lstrip()) > pind): j += 1
            L[found:j] = newl
        else:
            keys = [(i, L[i].strip().split(':')[0]) for i in range(pi + 1, pend) if L[i].strip() and len(L[i]) - len(L[i].lstrip()) == pind]
            pos = next((i for i, k in keys if k > prop), pend)
            L[pos:pos] = newl
    return nl.join(L)

za, zb = zipfile.ZipFile(A), zipfile.ZipFile(B)
changes = {}
for n in zb.namelist():
    if n.startswith('Controls\\') and za.read(n) != zb.read(n):
        da, db = json.loads(za.read(n)), json.loads(zb.read(n))
        ra, rb = rules(da), rules(db)
        changes[db['TopParent']['Name']] = [(c, p, v) for (c, p), v in rb.items() if ra.get((c, p)) != v]
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zo:
    for info in zb.infolist():
        data = zb.read(info.filename)
        m = re.match(r'Src\\(\w+)\.pa\.yaml$', info.filename)
        if m and m.group(1) in changes:
            data = patch_yaml(data.decode('utf-8'), changes[m.group(1)]).encode('utf-8')
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = info.external_attr; zi.create_system = info.create_system
        zo.writestr(zi, data)
print('ok', {k: len(v) for k, v in changes.items()})
