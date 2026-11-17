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
import re
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


def obter_coordenadas() -> tuple[str, str]:
    """CLIMA_LAT/CLIMA_LON validados. Aceita vírgula decimal (22,264 → 22.264)."""
    lat_txt = (obter("CLIMA_LAT", "-22.264") or "").strip().replace(",", ".")
    lon_txt = (obter("CLIMA_LON", "-49.136") or "").strip().replace(",", ".")
    try:
        lat, lon = float(lat_txt), float(lon_txt)
    except ValueError:
        raise ConfigError(
            f"CLIMA_LAT/CLIMA_LON inválidos: '{lat_txt}' / '{lon_txt}'. "
            "Use ponto (ou vírgula) decimal, ex: -22.264"
        ) from None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ConfigError(
            f"CLIMA_LAT/CLIMA_LON fora do intervalo: {lat}, {lon} "
            "(latitude -90..90, longitude -180..180)."
        )
    return lat_txt, lon_txt


def obter_destinatario() -> tuple[str, str]:
    """WHATSAPP_CHAT_ID + WAHA_SESSION validados.

    O destino pode ser um número privado (`...@c.us`) OU um grupo
    (`...@g.us`) — o formato é o mesmo, só muda o sufixo.
    """
    chat = (obter("WHATSAPP_CHAT_ID", obrigatorio=True) or "").strip()
    sessao = (obter("WAHA_SESSION", obrigatorio=True) or "").strip()

    if "AQUI" in chat.upper() or "AQUI" in sessao.upper():
        raise ConfigError(
            "Placeholder do .env.example ainda está no lugar — edite "
            "WHATSAPP_CHAT_ID e WAHA_SESSION no seu .env."
        )
    if not re.fullmatch(r"[^@\s]+@(c|g)\.us", chat):
        raise ConfigError(
            f"WHATSAPP_CHAT_ID inválido: '{chat}'. "
            "Use seu número (55 + DDD + número + @c.us) ou o ID de um grupo "
            "(120363...@g.us). Grupo: GET http://localhost:3000/api/{sessao}/groups"
        )
    if not re.fullmatch(r"[A-Za-z0-9_-]+", sessao):
        raise ConfigError(
            f"WAHA_SESSION inválido: '{sessao}'. Use apenas letras, números, _ e -."
        )
    return chat, sessao


# Carrega o .env assim que o módulo é importado
carregar_env()
