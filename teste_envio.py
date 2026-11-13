"""Teste de envio pro privado via WAHA (mesmo fluxo do n8n)."""
import json
import urllib.request

SESSAO = "session_01m7ah73fncj0kqfsf3kaqqtfb"
CHAT_ID = "5514999222285@c.us"
WAHA = "http://localhost:3000"


def post(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, resp.read().decode("utf-8")


def get(url):
    with urllib.request.urlopen(url, timeout=120) as resp:
        return resp.status, resp.read()


print("[1/2] Gerando relatorio na API local...")
req = urllib.request.Request("http://localhost:8000/relatorio", data=b"", method="POST")
with urllib.request.urlopen(req, timeout=180) as resp:
    rel = json.loads(resp.read().decode("utf-8"))

print(f"      ok={rel['ok']} em {rel.get('tempo_segundos')}s")

print("[2/2] Enviando imagem + texto pro WhatsApp...")
st, r1 = post(
    f"{WAHA}/api/sendImage",
    {
        "session": SESSAO,
        "chatId": CHAT_ID,
        "file": {
            "mimetype": "image/png",
            "filename": f"windy_{rel['data']}.png",
            "data": rel["imagem_base64"],
        },
        "caption": rel["resumo"],
    },
)
print(f"      sendImage -> HTTP {st}: {r1[:300]}")

st2, r2 = post(
    f"{WAHA}/api/sendText",
    {
        "session": SESSAO,
        "chatId": CHAT_ID,
        "text": "📄 *Relatório completo — Windy*\n\n" + rel["texto"],
    },
)
print(f"      sendText  -> HTTP {st2}: {r2[:300]}")
