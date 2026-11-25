"""Registra as fontes embutidas.

O KDP exige que todas as fontes estejam embutidas no PDF, por isso não
usamos as fontes padrão do PDF (Helvetica etc.), que não são embutidas.
DejaVu Sans é livre para redistribuição (veja fonts/LICENSE-DejaVu.txt).
"""
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_PASTA = Path(__file__).parent / "fonts"

FONTE = "DejaVuSans"
FONTE_NEGRITO = "DejaVuSans-Bold"

for _nome in (FONTE, FONTE_NEGRITO):
    if _nome not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(_nome, str(_PASTA / f"{_nome}.ttf")))
