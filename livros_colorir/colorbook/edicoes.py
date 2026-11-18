"""Edições de um mesmo livro: "só na frente" e "frente e verso".

Todo livro sai nas duas edições (cada uma numa subpasta de saida/<id>/):

  so_frente     um desenho por folha, verso em branco. Padrão dos livros de colorir
                da Amazon dos EUA e dos livros para canetinha. Dobra as páginas.
  frente_verso  desenhos dos dois lados. Padrão brasileiro (lápis de cor e giz de
                cera): metade das páginas, impressão sob demanda bem mais barata.

O tema pode ajustar cada edição com qualquer campo, por exemplo:

  "edicoes": {
    "so_frente":    {"verso_em_branco": true},
    "frente_verso": {"verso_em_branco": false, "formato": "a4",
                     "anuncio": {"descricao": "..."}}
  }

Campos com dicionário (capa, anuncio, colecao) são mesclados um nível: só as chaves
informadas mudam.
"""
from __future__ import annotations

import copy

EDICOES_PADRAO = {
    "so_frente": {"verso_em_branco": True},
    # Na frente e verso, páginas em branco são só ajuste de paginação: sem o aviso.
    "frente_verso": {"verso_em_branco": False, "aviso_verso": False},
}

NOMES = {"so_frente": "Só na frente", "frente_verso": "Frente e verso"}


def _mesclar(base: dict, ajustes: dict) -> dict:
    tema = copy.deepcopy(base)
    for chave, valor in ajustes.items():
        if isinstance(valor, dict) and isinstance(tema.get(chave), dict):
            tema[chave] = {**tema[chave], **copy.deepcopy(valor)}
        else:
            tema[chave] = copy.deepcopy(valor)
    return tema


def edicoes(tema: dict) -> dict[str, dict]:
    """Devolve {nome da edição: tema já ajustado para ela}."""
    conf = tema.get("edicoes") or EDICOES_PADRAO
    resultado = {}
    for nome, ajustes in conf.items():
        ajustes = {**EDICOES_PADRAO.get(nome, {}), **(ajustes or {})}
        t = _mesclar({k: v for k, v in tema.items() if k != "edicoes"}, ajustes)
        t["edicao"] = nome
        resultado[nome] = t
    return resultado


def nome_legivel(nome: str) -> str:
    return NOMES.get(nome, nome.replace("_", " "))
