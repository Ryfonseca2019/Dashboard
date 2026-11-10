"""Confere os PDFs gerados contra as regras do KDP antes do upload."""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from . import specs


def _fontes_nao_embutidas(leitor: PdfReader) -> set[str]:
    faltando: set[str] = set()
    for pagina in leitor.pages:
        recursos = pagina.get("/Resources") or {}
        fontes = recursos.get("/Font") or {}
        for ref in fontes.values():
            fonte = ref.get_object()
            nome = str(fonte.get("/BaseFont", "?"))
            descendentes = fonte.get("/DescendantFonts")
            alvo = descendentes[0].get_object() if descendentes else fonte
            desc = alvo.get("/FontDescriptor")
            desc = desc.get_object() if desc else None
            if not desc or not any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3")):
                faltando.add(nome)
    return faltando


def validar(tema: dict, miolo: Path, capa: Path, espec_capa: specs.EspecCapa) -> list[str]:
    """Devolve a lista de problemas encontrados (vazia = tudo certo)."""
    problemas: list[str] = []
    larg, alt = specs.formato(tema.get("formato", "8.5x11"))

    m = PdfReader(str(miolo))
    n = len(m.pages)
    if n < specs.MIN_PAGINAS:
        problemas.append(f"Miolo com {n} páginas; o mínimo do KDP é {specs.MIN_PAGINAS}.")
    if n > specs.MAX_PAGINAS:
        problemas.append(f"Miolo com {n} páginas; o máximo é {specs.MAX_PAGINAS}.")
    for i, pag in enumerate(m.pages, 1):
        w, h = float(pag.mediabox.width) / specs.POL, float(pag.mediabox.height) / specs.POL
        if abs(w - larg) > 0.01 or abs(h - alt) > 0.01:
            problemas.append(f"Página {i} com {w:.3f}×{h:.3f} pol; esperado {larg}×{alt}.")
            break
    if f := _fontes_nao_embutidas(m):
        problemas.append(f"Fontes não embutidas no miolo: {', '.join(sorted(f))}")

    c = PdfReader(str(capa))
    if len(c.pages) != 1:
        problemas.append("A capa deve ter exatamente 1 página.")
    w = float(c.pages[0].mediabox.width) / specs.POL
    h = float(c.pages[0].mediabox.height) / specs.POL
    if abs(w - espec_capa.largura_total) > 0.01 or abs(h - espec_capa.altura_total) > 0.01:
        problemas.append(
            f"Capa com {w:.3f}×{h:.3f} pol; esperado "
            f"{espec_capa.largura_total:.3f}×{espec_capa.altura_total:.3f}."
        )
    if f := _fontes_nao_embutidas(c):
        problemas.append(f"Fontes não embutidas na capa: {', '.join(sorted(f))}")
    return problemas
