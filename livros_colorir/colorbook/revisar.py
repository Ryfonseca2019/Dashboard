"""Revisão estética com a visão do Claude: o "segundo auditor".

    python -m colorbook revisar temas/primeiros_desenhos.json            # usa a API
    python -m colorbook revisar temas/primeiros_desenhos.json --simular  # sem chave

O auditor (auditar.py) mede o que dá para medir: traço, áreas, ocupação. Este
revisor responde o que só um olhar responde, página por página:
  - a criança reconhece a figura? bate com a legenda?
  - o desenho é bonito e simpático? (nota de 1 a 10)
  - é adequado à idade? tem algo estranho, assustador ou confuso?
  - o que melhorar?

Gera saida/<id>/revisao.md. Custo estimado: US$ 0,02 a 0,05 por página.
"""
from __future__ import annotations

import base64
import json
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .claude_cliente import MODELO, cliente, tem_chave
from .estilo import perfil_do_tema
from .miolo import planejar

DPI = 70  # suficiente para julgar o desenho; mantém o custo baixo

INSTRUCOES = """Você é diretor de arte de livros de colorir infantis vendidos na Amazon.
Avalie a página como um pai, uma mãe ou uma criança da faixa etária indicada a veria.
Seja exigente e concreto: compare com os livros de colorir mais bem avaliados do mercado.

Critérios:
- reconhecivel: a figura principal é reconhecível em 2 segundos e bate com o esperado.
- nota_visual (1 a 10): apelo e fofura do desenho, proporções, composição, acabamento.
  7 = bom o bastante para vender; 9+ = nível dos melhores do mercado.
- adequado_idade: áreas e detalhes adequados à faixa etária; nada assustador ou confuso.
- problemas: defeitos concretos e localizados (ex.: "a cauda parece solta do corpo",
  "o chapéu flutua acima da cabeça", "nuvens muito parecidas com as da página anterior").
  Lista vazia se não houver.
- sugestao: a mudança mais importante para subir a nota, em uma frase.
Responda em português do Brasil."""

ESQUEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["o_que_vejo", "reconhecivel", "nota_visual", "adequado_idade", "problemas",
                 "sugestao"],
    "properties": {
        "o_que_vejo": {"type": "string"},
        "reconhecivel": {"type": "boolean"},
        "nota_visual": {"type": "integer"},
        "adequado_idade": {"type": "boolean"},
        "problemas": {"type": "array", "items": {"type": "string"}},
        "sugestao": {"type": "string"},
    },
}


def _esperado(pag: dict) -> str:
    tipo = pag.get("tipo", "desenho")
    partes = [f"tipo de página: {tipo}"]
    for chave in ("desenho", "legenda", "figura", "letra", "palavra", "brinquedo", "acessorio",
                  "cena"):
        if pag.get(chave):
            partes.append(f"{chave}: {pag[chave]}")
    return "; ".join(partes)


def _avaliar(cli, imagem_png: bytes, pag: dict, faixa: str) -> dict:
    resposta = cli.beta.messages.create(
        model=MODELO,
        max_tokens=4000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=INSTRUCOES,
        output_config={"effort": "medium",
                       "format": {"type": "json_schema", "schema": ESQUEMA}},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": base64.b64encode(imagem_png).decode()}},
            {"type": "text", "text": f"Faixa etária: {faixa}. Esperado nesta página: "
                                     f"{_esperado(pag)}. Avalie a página."},
        ]}],
    )
    if resposta.stop_reason == "refusal":
        return {"erro": "o Claude recusou avaliar esta página"}
    if resposta.stop_reason == "max_tokens":
        return {"erro": "resposta cortada (limite de tamanho)"}
    texto = next(b.text for b in resposta.content if b.type == "text")
    dados = json.loads(texto)
    dados["_tokens"] = (resposta.usage.input_tokens, resposta.usage.output_tokens)
    return dados


def revisar(arquivo_tema: Path, saida: Path, simular: bool = False,
            paralelo: int = 4) -> dict:
    if not shutil.which("pdftoppm"):
        raise RuntimeError("A revisão precisa do pdftoppm (instale o poppler).")
    tema = json.loads(arquivo_tema.read_text(encoding="utf-8"))
    from .edicoes import edicoes

    pasta = saida / tema.get("id", arquivo_tema.stem)
    # As páginas de conteúdo são as mesmas nas duas edições: revisa a "só na frente".
    eds = edicoes(tema)
    nome_ed = "so_frente" if "so_frente" in eds else next(iter(eds))
    tema = eds[nome_ed]
    miolo = pasta / nome_ed / "miolo.pdf"
    if not miolo.exists():
        raise RuntimeError(f"Gere o livro antes: python -m colorbook construir {arquivo_tema}")
    faixa = tema.get("faixa_etaria") or perfil_do_tema(tema).nome
    conteudo = [(n, p) for n, p in enumerate(planejar(tema), 1)
                if not p["tipo"].startswith("_")]

    with tempfile.TemporaryDirectory() as tmp:
        imagens = []
        for numero, _ in conteudo:
            alvo = Path(tmp) / f"p{numero}"
            subprocess.run(["pdftoppm", "-png", "-r", str(DPI), "-singlefile", "-f",
                            str(numero), "-l", str(numero), str(miolo), str(alvo)], check=True)
            imagens.append(alvo.with_suffix(".png").read_bytes())

    if simular or not tem_chave():
        # Estimativa: imagem ≈ largura × altura / 750 tokens; texto + resposta + raciocínio.
        tokens_img = (8.5 * DPI) * (11 * DPI) / 750
        entrada = len(conteudo) * (tokens_img + 700)
        saida_tok = len(conteudo) * 1500
        custo = entrada / 1e6 * 4 + saida_tok / 1e6 * 20  # preço por milhão de tokens (Opus 5.5)
        return {"simulado": True, "paginas": len(conteudo), "custo_estimado_usd": custo,
                "sem_chave": not tem_chave()}

    cli = cliente()
    with ThreadPoolExecutor(max_workers=paralelo) as ex:
        resultados = list(ex.map(lambda args: _avaliar(cli, args[0], args[1][1], faixa),
                                 zip(imagens, conteudo)))
    relatorio = _relatorio(tema, conteudo, resultados)
    (pasta / "revisao.md").write_text(relatorio, encoding="utf-8")
    (pasta / "revisao.json").write_text(json.dumps(
        [{"pagina": n, **r} for (n, _), r in zip(conteudo, resultados)],
        ensure_ascii=False, indent=2), encoding="utf-8")
    notas = [r["nota_visual"] for r in resultados if "nota_visual" in r]
    return {"simulado": False, "paginas": len(conteudo),
            "media": sum(notas) / len(notas) if notas else 0,
            "abaixo_de_7": sum(1 for n in notas if n < 7),
            "nao_reconhecidas": sum(1 for r in resultados if r.get("reconhecivel") is False),
            "relatorio": pasta / "revisao.md"}


def _relatorio(tema: dict, conteudo, resultados) -> str:
    notas = [r["nota_visual"] for r in resultados if "nota_visual" in r]
    media = sum(notas) / len(notas) if notas else 0
    linhas = [
        f"# Revisão estética — {tema['titulo']}", "",
        f"**Nota visual média: {media:.1f}/10** · {len(conteudo)} páginas · "
        f"{sum(1 for n in notas if n < 7)} abaixo de 7 · "
        f"{sum(1 for r in resultados if r.get('reconhecivel') is False)} não reconhecidas",
        "", "Meta para vender bem: média ≥ 7,5 e nenhuma página abaixo de 6.", "",
        "| Pág. | Esperado | O Claude vê | Nota | Reconhece | Idade | Problemas | Sugestão |",
        "|---|---|---|---|---|---|---|---|",
    ]
    ordem = sorted(zip(conteudo, resultados), key=lambda x: x[1].get("nota_visual", 0))
    for (numero, pag), r in ordem:
        if "erro" in r:
            linhas.append(f"| {numero} | {_esperado(pag)} | — | — | — | — | {r['erro']} | |")
            continue
        linhas.append(
            f"| {numero} | {pag.get('legenda') or pag.get('desenho') or pag.get('tipo')} | "
            f"{r['o_que_vejo']} | {r['nota_visual']} | {'sim' if r['reconhecivel'] else '**não**'} | "
            f"{'sim' if r['adequado_idade'] else '**não**'} | {' '.join(r['problemas']) or '—'} | "
            f"{r['sugestao']} |")
    return "\n".join(linhas) + "\n"
