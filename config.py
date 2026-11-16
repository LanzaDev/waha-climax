"""
Carrega as configurações do projeto a partir do arquivo .env.

Primeira utilização:
    copy .env.example .env      (Windows)
    cp .env.example .env        (Linux/macOS)
    # edite o .env com seus dados

O .env é local e está no .gitignore — número de telefone, sessão do WAHA
e demais dados pessoais nunca sobem pro GitHub.

Regras:
  • Variáveis já presentes no ambiente têm prioridade (o .env não
    sobrescreve), então dá pra sobrescrever pelo terminal ou pelo Docker.
  • Sem dependências externas (não precisa de python-dotenv).
"""

from __future__ import annotations

import os
from pathlib import Path

PASTA_RAIZ = Path(__file__).resolve().parent
ARQUIVO_ENV = PASTA_RAIZ / ".env"


class ConfigError(RuntimeError):
    """Configuração ausente ou inválida."""


def carregar_env(caminho: Path = ARQUIVO_ENV) -> bool:
    """Lê um .env simples (CHAVE=VALOR, aceita #comentários). True se o arquivo existia."""
    caminho = Path(caminho)
    if not caminho.is_file():
        return False
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if chave and chave not in os.environ:
            os.environ[chave] = valor
    return True


def obter(chave: str, padrao: str | None = None, obrigatorio: bool = False) -> str | None:
    """Devolve a variável de ambiente (com o .env já carregado)."""
    valor = os.environ.get(chave, padrao)
    if obrigatorio and not valor:
        raise ConfigError(
            f"Variável '{chave}' não definida. Copie .env.example para .env "
            f"(na pasta {PASTA_RAIZ}) e preencha com seus valores."
        )
    return valor


def obter_int(chave: str, padrao: int) -> int:
    """Como obter(), mas convertendo para int (cai no padrão se o valor for inválido)."""
    bruto = os.environ.get(chave)
    if bruto is None or not str(bruto).strip():
        return padrao
    try:
        return int(str(bruto).strip())
    except ValueError:
        print(f"[config] Aviso: '{chave}={bruto}' não é um número — usando {padrao}.")
        return padrao


# Carrega o .env assim que o módulo é importado
carregar_env()
