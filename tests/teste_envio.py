"""Teste de envio pro privado via WAHA (mesmo fluxo do n8n).

Envia apenas a IMAGEM do mapa (com o resumo na legenda), igual ao workflow
do n8n - o relatorio completo em texto nao e enviado.

Pré-requisitos:
    1. API rodando (iniciar.bat)
    2. .env configurado (copy .env.example .env e preencha)

Uso:
    python tests/teste_envio.py
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Rodando de dentro de tests/, o modulo config.py fica um nivel acima:
# adiciona a raiz do projeto no sys.path para o import funcionar de qualquer
# lugar (python tests/teste_envio.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import ConfigError, obter, obter_destinatario, obter_int  # noqa: E402

WAHA = obter("WAHA_URL", "http://localhost:3000") or "http://localhost:3000"
PORTA_API = obter_int("CLIMA_PORT", 8000)


def post(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, resp.read().decode("utf-8")


def main():
    try:
        chat_id, sessao = obter_destinatario()
    except ConfigError as erro:
        print(f"ERRO DE CONFIGURAÇÃO: {erro}")
        raise SystemExit(1)

    print("[1/2] Gerando relatorio na API local...")
    try:
        req = urllib.request.Request(
            f"http://localhost:{PORTA_API}/relatorio", data=b"", method="POST"
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            rel = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as erro:
        print(f"ERRO: API não respondeu em :{PORTA_API} — execute 'iniciar.bat' antes. ({erro})")
        raise SystemExit(1)

    if not rel.get("ok"):
        print(f"ERRO na geração do relatorio: {rel.get('erro')}")
        raise SystemExit(1)
    print(f"      ok={rel['ok']} em {rel.get('tempo_segundos')}s")

    print(f"[2/2] Enviando imagem pro WhatsApp ({chat_id})...")
    st, r1 = post(
        f"{WAHA}/api/sendImage",
        {
            "session": sessao,
            "chatId": chat_id,
            "file": {
                "mimetype": "image/png",
                "filename": f"windy_{rel['data']}.png",
                "data": rel["imagem_base64"],
            },
            "caption": rel["resumo"],
        },
    )
    print(f"      sendImage -> HTTP {st}: {r1[:300]}")

    if st == 201:
        print("\nTESTE OK — imagem entregue ao WhatsApp.")
    else:
        print("\nTESTE COM PROBLEMA — veja os status HTTP acima.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
