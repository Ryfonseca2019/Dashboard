"""Gera os textos do anúncio (Amazon KDP, Etsy, Mercado Livre) a partir do tema,
já conferindo os limites de cada campo."""
from __future__ import annotations

import json
from pathlib import Path

from . import specs

LIMITES = {
    "titulo_mais_subtitulo": 200,   # KDP: título + subtítulo
    "descricao": 4000,              # KDP: descrição
    "palavras_chave": 7,            # KDP: 7 campos
    "tamanho_palavra_chave": 50,    # KDP: caracteres por campo
    "titulo_etsy": 140,
    "tags_etsy": 13,
    "tamanho_tag_etsy": 20,
    "titulo_mercado_livre": 60,
}


def _avisos(tema: dict, anuncio: dict) -> list[str]:
    avisos = []
    titulo_sub = f"{tema['titulo']}: {tema.get('subtitulo', '')}"
    if len(titulo_sub) > LIMITES["titulo_mais_subtitulo"]:
        avisos.append(f"Título + subtítulo têm {len(titulo_sub)} caracteres (máx. 200 no KDP).")
    if len(anuncio.get("descricao", "")) > LIMITES["descricao"]:
        avisos.append("Descrição passa de 4000 caracteres (limite do KDP).")
    chaves = anuncio.get("palavras_chave", [])
    if len(chaves) > LIMITES["palavras_chave"]:
        avisos.append(f"{len(chaves)} palavras-chave; o KDP aceita 7 (as extras foram cortadas).")
    for k in chaves:
        if len(k) > LIMITES["tamanho_palavra_chave"]:
            avisos.append(f"Palavra-chave longa demais (máx. 50): '{k}'")
    for marca in ("disney", "pokemon", "pokémon", "marvel", "barbie", "peppa", "patrulha canina"):
        texto = json.dumps(anuncio, ensure_ascii=False).lower() + tema["titulo"].lower()
        if marca in texto:
            avisos.append(f"Menção a marca registrada ('{marca}'): risco de bloqueio por direitos.")
    return avisos


def gerar_anuncio(tema: dict, num_paginas: int, espec_capa: specs.EspecCapa, pasta: Path) -> dict:
    anuncio = tema.get("anuncio", {})
    chaves = anuncio.get("palavras_chave", [])[: LIMITES["palavras_chave"]]
    tags = [t[: LIMITES["tamanho_tag_etsy"]] for t in anuncio.get("tags_etsy", chaves)]
    titulo_ml = f"Livro de Colorir Infantil {tema['titulo']}"[: LIMITES["titulo_mercado_livre"]]
    dados = {
        "kdp": {
            "titulo": tema["titulo"],
            "subtitulo": tema.get("subtitulo", ""),
            "autor": tema.get("autor", ""),
            "descricao": anuncio.get("descricao", ""),
            "palavras_chave": chaves,
            "categorias": anuncio.get("categorias", []),
            "faixa_etaria": tema.get("faixa_etaria", ""),
            "conteudo_gerado_por_ia": anuncio.get("conteudo_ia", {
                # Na dúvida, declare "Sim". Desenhos e textos criados pelo Claude contam
                # como conteúdo gerado por IA pelas regras do KDP.
                "texto": "Sim, gerado por IA (revisado por pessoa)",
                "imagens": "Sim, gerado por IA (revisado por pessoa)",
            }),
            "formato": tema.get("formato", "8.5x11"),
            "papel": tema.get("papel", "branco"),
            "tinta": "preto e branco",
            "sangria": "sem sangria (miolo)",
            "acabamento_capa": anuncio.get("acabamento_capa", "fosco"),
            "num_paginas": num_paginas,
            "preco_sugerido_usd": anuncio.get("preco_sugerido_usd"),
        },
        "etsy_pdf_digital": {
            "titulo": f"{tema['titulo']} – Páginas para colorir em PDF"[: LIMITES["titulo_etsy"]],
            "tags": tags[: LIMITES["tags_etsy"]],
            "descricao": anuncio.get("descricao", ""),
        },
        "mercado_livre": {"titulo": titulo_ml, "descricao": anuncio.get("descricao", "")},
        "capa": {
            "largura_total_pol": round(espec_capa.largura_total, 4),
            "altura_total_pol": round(espec_capa.altura_total, 4),
            "lombada_pol": round(espec_capa.lombada, 4),
            "texto_na_lombada": espec_capa.aceita_texto_lombada,
        },
        "avisos": _avisos(tema, anuncio),
    }
    (pasta / "anuncio.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    (pasta / "anuncio.md").write_text(_markdown(dados), encoding="utf-8")
    return dados


def _markdown(d: dict) -> str:
    k = d["kdp"]
    linhas = [
        f"# {k['titulo']}",
        "",
        f"**Subtítulo:** {k['subtitulo']}  ",
        f"**Autor:** {k['autor']}  ",
        f"**Faixa etária:** {k['faixa_etaria']}  ",
        f"**Páginas:** {k['num_paginas']} · **Formato:** {k['formato']} pol · "
        f"**Papel:** {k['papel']} · **Capa:** {k['acabamento_capa']}",
        "",
        "## Descrição (copiar no KDP)",
        "",
        k["descricao"],
        "",
        "## Palavras-chave (uma por campo no KDP)",
        "",
        *[f"{i}. {p}" for i, p in enumerate(k["palavras_chave"], 1)],
        "",
        "## Categorias sugeridas",
        "",
        *[f"- {c}" for c in k["categorias"]],
        "",
        "## Declaração de conteúdo de IA (pergunta obrigatória no KDP)",
        "",
        f"- Texto: {k['conteudo_gerado_por_ia']['texto']}",
        f"- Imagens: {k['conteudo_gerado_por_ia']['imagens']}",
        "",
        "## Capa",
        "",
        f"- Arquivo: {d['capa']['largura_total_pol']} × {d['capa']['altura_total_pol']} pol "
        f"(lombada {d['capa']['lombada_pol']} pol)",
        f"- Texto na lombada: {'sim' if d['capa']['texto_na_lombada'] else 'não (menos de 79 páginas)'}",
        "",
        "## Etsy (PDF digital)",
        "",
        f"**Título:** {d['etsy_pdf_digital']['titulo']}  ",
        f"**Tags:** {', '.join(d['etsy_pdf_digital']['tags'])}",
        "",
        "## Mercado Livre",
        "",
        f"**Título:** {d['mercado_livre']['titulo']}",
        "",
    ]
    if d["avisos"]:
        linhas += ["## ⚠️ Avisos", "", *[f"- {a}" for a in d["avisos"]], ""]
    return "\n".join(linhas)
