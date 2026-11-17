"""Ilustrações vindas de uma ferramenta de geração de imagens (qualquer uma).

Fluxo:
  1. python -m colorbook pedidos-ilustracao temas/x.json
       → saida/<id>/pedidos_ilustracao.md com um pedido (prompt) por desenho,
         já no padrão de livro de colorir para a idade do livro.
  2. Gere as imagens na ferramenta que preferir e salve cada uma com o nome do
     desenho que ela substitui (ex.: gato.png, dinossauro.png) numa pasta.
  3. python -m colorbook importar-ilustracoes pasta/ temas/x.json
       → limpa o traço de cada imagem e troca a página daquele desenho por ela.

A limpeza deixa a imagem com cara de página de colorir de verdade: preto e branco
puro, sem sujeira, contornos fechados, traço grosso o bastante para a idade e
áreas pequenas demais preenchidas de preto (mesma regra do auditor).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage

from .estilo import Perfil, perfil_do_tema

DPI_SAIDA = 300
PX_POR_PT = DPI_SAIDA / 72
PX2_POR_CM2 = (DPI_SAIDA / 2.54) ** 2

DESCRICOES_EN = {
    "sol": "a smiling sun", "gato": "a cute cat sitting", "cachorro": "a happy puppy",
    "coelho": "a bunny", "casa": "a little house", "flor": "a big flower",
    "arvore": "a tree", "tartaruga": "a turtle", "elefante": "a baby elephant",
    "dinossauro": "a friendly baby dinosaur", "carro": "a small car", "trem": "a toy train",
    "caracol": "a snail", "joaninha": "a ladybug", "borboleta": "a butterfly",
    "passarinho": "a little bird on a branch", "coruja": "an owl on a branch",
    "baloes": "three balloons", "sorvete": "an ice cream cone", "maca": "an apple",
    "peixe": "a fish", "polvo": "an octopus", "barco": "a sailboat", "sapo": "a frog",
    "pinguim": "a penguin", "foguete": "a rocket", "estrela": "a smiling star",
    "arco_iris": "a rainbow with clouds", "coracao": "a heart",
}
CENARIO_EN = {
    "campo": "in a simple grassy meadow, with a cloud and the sun in the sky",
    "mar": "underwater with a few bubbles and seaweed",
    "mar_superficie": "on calm waves",
    "lago": "on a lily pad in a pond",
    "neve": "on snowy ground with a few snowflakes",
    "espaco": "in space with a planet and a few stars",
    "nenhum": "",
}


def _prompt(desenho: str, cena: str, perfil: Perfil, idade: str) -> str:
    assunto = DESCRICOES_EN.get(desenho, desenho.replace("_", " "))
    detalhe = ("very simple, few large areas, extra thick outlines"
               if perfil.area_min_cm2 >= 0.5 else
               "moderate detail, medium-thick outlines")
    fundo = CENARIO_EN.get(cena, "")
    return (f"Children's coloring book page for ages {idade}: {assunto}"
            + (f", {fundo}" if fundo else "")
            + f". Cute friendly style, {detalhe}. Clean closed black outlines only, "
            "pure white background, no shading, no gray, no hatching, no text, no border, "
            "full-page composition in portrait orientation.")


def gerar_pedidos(arquivo_tema: Path, saida: Path) -> Path:
    from .cenas import CENA_PADRAO

    tema = json.loads(arquivo_tema.read_text(encoding="utf-8"))
    perfil = perfil_do_tema(tema)
    idade = tema.get("faixa_etaria", "3 to 6").replace(" a ", " to ").replace(" anos", "")
    pasta = saida / tema.get("id", arquivo_tema.stem)
    pasta.mkdir(parents=True, exist_ok=True)
    vistos, linhas = set(), [
        f"# Pedidos de ilustração — {tema['titulo']}", "",
        "Gere cada imagem na ferramenta que preferir e salve com o nome indicado "
        "(ex.: `gato.png`). Depois rode `python -m colorbook importar-ilustracoes "
        f"PASTA {arquivo_tema}`.", "",
        "Dicas: peça formato retrato (proporção 3:4); gere 2 a 4 opções e escolha a mais "
        "simples; descarte imagens com texto, sombras ou cinza.", "",
    ]
    for pag in tema["paginas"]:
        if pag.get("tipo", "desenho") != "desenho" or pag["desenho"] in vistos:
            continue
        vistos.add(pag["desenho"])
        cena = pag.get("cena") or (CENA_PADRAO.get(pag["desenho"], "nenhum")
                                   if tema.get("cenarios") else "nenhum")
        linhas += [f"## {pag['desenho']}.png — {pag.get('legenda', '')}", "",
                   "```", _prompt(pag["desenho"], cena, perfil, idade), "```", ""]
    destino = pasta / "pedidos_ilustracao.md"
    destino.write_text("\n".join(linhas), encoding="utf-8")
    return destino


def limpar_imagem(entrada: Path, saida: Path, perfil: Perfil) -> dict:
    """Transforma uma ilustração qualquer em página de colorir limpa (PNG 1 bit)."""
    img = ImageOps.exif_transpose(Image.open(entrada)).convert("L")
    # Trabalha em ~300 dpi para uma área útil de ~7 x 9 pol.
    escala = min(2100 / img.width, 2700 / img.height)
    if abs(escala - 1) > 0.05:
        img = img.resize((round(img.width * escala), round(img.height * escala)),
                         Image.LANCZOS)
    cinza = np.asarray(ImageOps.autocontrast(img, cutoff=1), dtype=np.uint8)

    # 1. Preto e branco: limiar de Otsu (separa traço do fundo automaticamente).
    hist = np.bincount(cinza.ravel(), minlength=256).astype(float)
    total, soma = hist.sum(), (np.arange(256) * hist).sum()
    melhor, limiar, peso_b, soma_b = 0.0, 128, 0.0, 0.0
    for t in range(256):
        peso_b += hist[t]
        if peso_b == 0 or peso_b == total:
            continue
        soma_b += t * hist[t]
        mb, mf = soma_b / peso_b, (soma - soma_b) / (total - peso_b)
        var = peso_b * (total - peso_b) * (mb - mf) ** 2
        if var > melhor:
            melhor, limiar = var, t
    # Histerese: um pixel cinza só vira traço se estiver ligado a um traço escuro de
    # verdade. Sombreados e manchas cinza soltas (comuns em imagens geradas) somem.
    fraco = cinza < limiar
    forte = cinza < min(limiar, 90)
    rotulos_fracos, _ = ndimage.label(fraco)
    com_nucleo = np.unique(rotulos_fracos[forte])
    tinta = np.isin(rotulos_fracos, com_nucleo[com_nucleo > 0])
    # Cinza "grosso" (preenchimento, não linha) também é sombreado, mesmo encostado
    # num contorno: some. Traço escuro (olhos, detalhes sólidos) não é afetado.
    medio = fraco & ~forte
    sombreado = ndimage.binary_opening(medio, structure=np.ones((7, 7)))
    sombreado = ndimage.binary_dilation(sombreado, iterations=2) & medio
    tinta &= ~sombreado

    # 2. Remove sujeira (pontinhos soltos).
    rot, n = ndimage.label(tinta)
    if n:
        tam = np.bincount(rot.ravel())
        minimo = 0.02 * PX2_POR_CM2
        tinta &= tam[rot] >= minimo

    # 3. Fecha falhas pequenas no contorno e engrossa o traço até o mínimo da idade.
    tinta = ndimage.binary_closing(tinta, structure=np.ones((5, 5)))
    alvo = perfil.traco_min_pt * PX_POR_PT * 1.3
    espessura = _espessura_mediana(tinta)
    engrossou = 0
    if espessura and espessura < alvo:
        engrossou = int(np.ceil((alvo - espessura) / 2))
        tinta = ndimage.binary_dilation(tinta, iterations=engrossou)

    # 4. Áreas pequenas demais para pintar viram preto sólido.
    fundo, n = ndimage.label(~tinta)
    preenchidas = 0
    if n:
        tam = np.bincount(fundo.ravel())
        borda = set(np.unique(np.concatenate([fundo[0], fundo[-1], fundo[:, 0], fundo[:, -1]])))
        pequenas = [i for i in range(1, n + 1)
                    if i not in borda and tam[i] < perfil.area_min_cm2 * PX2_POR_CM2]
        preenchidas = len(pequenas)
        if pequenas:
            tinta |= np.isin(fundo, pequenas)

    # 5. Recorta a sobra branca e salva em 1 bit.
    linhas, colunas = np.where(tinta.any(axis=1))[0], np.where(tinta.any(axis=0))[0]
    if len(linhas):
        m = 20
        tinta = tinta[max(0, linhas[0] - m): linhas[-1] + m, max(0, colunas[0] - m): colunas[-1] + m]
    Image.fromarray(np.where(tinta, 0, 255).astype(np.uint8)).convert("1").save(
        saida, dpi=(DPI_SAIDA, DPI_SAIDA))
    return {"limiar": int(limiar), "espessura_px": espessura, "engrossou_px": engrossou,
            "areas_preenchidas": preenchidas}


def _espessura_mediana(tinta: np.ndarray) -> float:
    """Espessura típica do traço: o dobro da distância do esqueleto até a borda."""
    if not tinta.any():
        return 0.0
    dist = ndimage.distance_transform_edt(tinta)
    # Pixels "centrais" do traço: máximos locais da distância.
    centro = (dist == ndimage.maximum_filter(dist, size=3)) & tinta
    valores = dist[centro]
    return float(np.median(valores) * 2) if valores.size else 0.0


def importar(pasta: Path, arquivo_tema: Path) -> tuple[Path, list[str]]:
    """Limpa as imagens da pasta e cria um tema novo (<tema>_ilustrado.json) em que as
    páginas dos desenhos correspondentes usam as imagens. O tema original fica intacto."""
    tema = json.loads(arquivo_tema.read_text(encoding="utf-8"))
    perfil = perfil_do_tema(tema)
    destino = arquivo_tema.parent / "imagens" / tema.get("id", arquivo_tema.stem)
    destino.mkdir(parents=True, exist_ok=True)
    trocadas = []
    for arq in sorted(pasta.iterdir()):
        if arq.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            continue
        nome = arq.stem
        limpa = destino / f"{nome}.png"
        info = limpar_imagem(arq, limpa, perfil)
        rel = limpa.relative_to(arquivo_tema.parent).as_posix()
        for i, pag in enumerate(tema["paginas"]):
            if pag.get("tipo", "desenho") == "desenho" and pag.get("desenho") == nome:
                tema["paginas"][i] = {"tipo": "imagem", "arquivo": rel,
                                      "legenda": pag.get("legenda"), "origem": nome}
        trocadas.append(f"{nome}: engrossou {info['engrossou_px']} px, "
                        f"{info['areas_preenchidas']} área(s) pequena(s) preenchida(s)")
    tema["id"] = f"{tema.get('id', arquivo_tema.stem)}_ilustrado"
    novo = arquivo_tema.with_name(f"{arquivo_tema.stem}_ilustrado.json")
    novo.write_text(json.dumps(tema, ensure_ascii=False, indent=2), encoding="utf-8")
    return novo, trocadas
