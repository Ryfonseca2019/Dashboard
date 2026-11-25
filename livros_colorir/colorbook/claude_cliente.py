"""Cliente da API do Claude usado pelo projeto (criar-tema e revisão estética).

A chave é lida, nesta ordem, de:
  COLORBOOK_ANTHROPIC_KEY  (recomendado no Claude Code na nuvem, para não confundir
                            com a autenticação do próprio Claude Code)
  ANTHROPIC_API_KEY        (padrão, no seu computador)

Crie a chave em https://console.anthropic.com (Billing → créditos; API Keys → Create Key).
Nunca coloque a chave no código nem em arquivos do repositório.
"""
from __future__ import annotations

import os

MODELO = "claude-opus-5-5"

AJUDA_CHAVE = (
    "Chave da API do Claude não encontrada.\n"
    "  1. Crie a chave em https://console.anthropic.com (Billing → créditos; "
    "API Keys → Create Key).\n"
    "  2. No seu computador: export ANTHROPIC_API_KEY=sk-ant-...\n"
    "     No Claude Code na nuvem: configure a variável COLORBOOK_ANTHROPIC_KEY no ambiente\n"
    "     (menu do ambiente → Edit → Environment variables) e abra uma sessão nova.\n"
    "  Use --simular para testar sem chave."
)


def tem_chave() -> bool:
    return bool(os.environ.get("COLORBOOK_ANTHROPIC_KEY") or os.environ.get("ANTHROPIC_API_KEY"))


def cliente():
    import anthropic  # import tardio: só é preciso para os comandos que usam o Claude

    chave = os.environ.get("COLORBOOK_ANTHROPIC_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not chave:
        raise RuntimeError(AJUDA_CHAVE)
    # Com COLORBOOK_ANTHROPIC_KEY, fala direto com a API pública (no Claude Code na nuvem,
    # ANTHROPIC_BASE_URL aponta para a conexão do próprio Claude Code).
    if os.environ.get("COLORBOOK_ANTHROPIC_KEY"):
        base = os.environ.get("COLORBOOK_ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        return anthropic.Anthropic(api_key=chave, base_url=base)
    return anthropic.Anthropic(api_key=chave)
