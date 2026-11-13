"""Cria um tema novo (JSON) a partir de uma ideia, usando a API do Claude.

    python -m colorbook criar-tema "animais do Pantanal para 3 a 5 anos"

O Claude escolhe os desenhos entre os que existem na biblioteca, escreve
legendas, títulos, descrição de venda e palavras-chave. O resultado é um
JSON comum em temas/, que você pode revisar antes de construir o livro.

Requer o pacote `anthropic` e credenciais (ANTHROPIC_API_KEY ou `ant auth login`).
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from .atividades import FIGURAS_PONTOS
from .desenhos import DESENHOS

MODELO = "claude-opus-5-5"

INSTRUCOES = """Você planeja livros de colorir infantis para vender na Amazon KDP, Etsy e \
Mercado Livre, em português do Brasil.

Regras:
- Use apenas os desenhos da lista permitida; você pode repetir alguns, com legendas diferentes.
- Monte de 20 a 40 páginas de conteúdo, na maioria "desenho". Intercale uma atividade a
  cada 3 ou 4 desenhos, variando os tipos:
  "labirinto" (use "inicio" e "fim" com dois desenhos da lista, ex.: coelho e maca),
  "ligar_pontos" (use "figura"), "diferencas" (use "desenho" como cena),
  "complete" (use um "desenho" simétrico, como borboleta, coruja ou estrela) e
  "cubra" (use "desenho"). Também pode usar "mandala".
- "semente" é um inteiro qualquer (muda labirintos, diferenças e mandalas) e "nivel"
  vai de 1 (2 a 5 anos) a 3 (7 a 10 anos), adequado à faixa etária.
- Campos que não se aplicam ao tipo da página ficam como texto vazio.
- Legendas curtas (1 a 3 palavras), positivas e fáceis de ler.
- Nunca cite personagens, marcas ou franquias registradas.
- Descrição de venda: 3 a 5 parágrafos curtos, com benefícios para pais e mães
  (coordenação motora, criatividade, tempo longe das telas), o formato (8,5 x 11 pol,
  um desenho por folha com verso em branco) e a faixa etária. Sem promessas exageradas.
- Exatamente 7 palavras-chave de até 50 caracteres, como as pessoas buscam na Amazon.
- Até 13 tags para Etsy, de até 20 caracteres cada.
- Cores da capa em hexadecimal, alegres e com bom contraste com texto branco contornado.
"""


def _esquema() -> dict:
    nomes = sorted(DESENHOS)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["titulo", "subtitulo", "faixa_etaria", "paginas", "capa", "anuncio"],
        "properties": {
            "titulo": {"type": "string"},
            "subtitulo": {"type": "string"},
            "faixa_etaria": {"type": "string"},
            "paginas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["tipo", "desenho", "legenda", "semente", "nivel", "inicio",
                                 "fim", "figura"],
                    "properties": {
                        "tipo": {"type": "string", "enum": [
                            "desenho", "mandala", "labirinto", "ligar_pontos", "diferencas",
                            "complete", "cubra"]},
                        "desenho": {"type": "string", "enum": nomes + [""]},
                        "inicio": {"type": "string", "enum": nomes + [""]},
                        "fim": {"type": "string", "enum": nomes + [""]},
                        "figura": {"type": "string", "enum": sorted(FIGURAS_PONTOS) + [""]},
                        "legenda": {"type": "string"},
                        "semente": {"type": "integer"},
                        "nivel": {"type": "integer", "enum": [1, 2, 3]},
                    },
                },
            },
            "capa": {
                "type": "object",
                "additionalProperties": False,
                "required": ["cor_fundo", "desenhos", "texto_contracapa"],
                "properties": {
                    "cor_fundo": {"type": "string"},
                    "desenhos": {"type": "array", "items": {"type": "string", "enum": nomes}},
                    "texto_contracapa": {"type": "string"},
                },
            },
            "anuncio": {
                "type": "object",
                "additionalProperties": False,
                "required": ["descricao", "descricao_curta", "palavras_chave", "tags_etsy",
                             "categorias"],
                "properties": {
                    "descricao": {"type": "string"},
                    "descricao_curta": {"type": "string"},
                    "palavras_chave": {"type": "array", "items": {"type": "string"}},
                    "tags_etsy": {"type": "array", "items": {"type": "string"}},
                    "categorias": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    }


def _limpar_paginas(paginas: list[dict]) -> list[dict]:
    """Mantém só os campos que cada tipo usa e descarta páginas incompletas."""
    limpas = []
    for p in paginas:
        tipo = p["tipo"]
        nivel = {"nivel": p["nivel"]}
        if tipo == "mandala":
            limpas.append({"tipo": "mandala", "semente": p["semente"], **nivel,
                           "legenda": p.get("legenda") or None})
        elif tipo == "desenho" and p.get("desenho"):
            limpas.append({"tipo": "desenho", "desenho": p["desenho"], "legenda": p["legenda"]})
        elif tipo == "labirinto" and p.get("inicio") and p.get("fim"):
            limpas.append({"tipo": "labirinto", "semente": p["semente"], **nivel,
                           "inicio": p["inicio"], "fim": p["fim"]})
        elif tipo == "ligar_pontos" and p.get("figura"):
            limpas.append({"tipo": "ligar_pontos", "figura": p["figura"], **nivel})
        elif tipo == "diferencas" and p.get("desenho"):
            limpas.append({"tipo": "diferencas", "desenho": p["desenho"],
                           "semente": p["semente"], **nivel})
        elif tipo in ("complete", "cubra") and p.get("desenho"):
            limpas.append({"tipo": tipo, "desenho": p["desenho"]})
    return limpas


def _slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")[:50] or "tema"


def criar_tema(ideia: str, autor: str, pasta_temas: Path) -> Path:
    import anthropic  # import tardio: só é preciso para este comando

    client = anthropic.Anthropic()
    resposta = client.beta.messages.create(
        model=MODELO,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=INSTRUCOES,
        output_config={"effort": "medium",
                       "format": {"type": "json_schema", "schema": _esquema()}},
        messages=[{
            "role": "user",
            "content": (f"Ideia do livro: {ideia}\n\n"
                        f"Desenhos permitidos: {', '.join(sorted(DESENHOS))}"),
        }],
    )
    if resposta.stop_reason == "refusal":
        raise RuntimeError("O Claude recusou o pedido. Reformule a ideia do livro.")
    if resposta.stop_reason == "max_tokens":
        raise RuntimeError("Resposta cortada por limite de tamanho; tente uma ideia menor.")
    texto = next(b.text for b in resposta.content if b.type == "text")
    dados = json.loads(texto)

    tema = {
        "id": _slug(dados["titulo"]),
        "titulo": dados["titulo"],
        "subtitulo": dados["subtitulo"],
        "autor": autor,
        "faixa_etaria": dados["faixa_etaria"],
        "formato": "8.5x11",
        "papel": "branco",
        "gerado_por": "claude",
        "paginas": _limpar_paginas(dados["paginas"]),
        "capa": dados["capa"],
        "anuncio": dados["anuncio"],
    }
    pasta_temas.mkdir(parents=True, exist_ok=True)
    destino = pasta_temas / f"{tema['id']}.json"
    destino.write_text(json.dumps(tema, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino
