"""
API HTTP local do relatório Windy.

Uso:
    python api.py                # sobe em http://localhost:8000
    GET|POST http://localhost:8000/relatorio

Resposta (JSON):
    { ok, local, data, horario, url, resumo, texto, imagem_base64, ... }

Variáveis de ambiente:
    CLIMA_PORT      porta do servidor (padrão 8000)
    CLIMA_HEADLESS  "0" abre a janela do navegador (padrão: headless)
    CLIMA_WAIT_MS   tempo de espera do carregamento em ms (padrão 15000)
"""

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from print import gerar_relatorio

PORTA = int(os.environ.get("CLIMA_PORT", "8000"))

# Playwright + Chromium pesam; evita duas execuções simultâneas
_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def _responder(self, status, corpo):
        body = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _gerar(self):
        if not _lock.acquire(blocking=False):
            self._responder(429, {"ok": False, "erro": "Já existe um relatório em andamento. Tente de novo em instantes."})
            return
        try:
            inicio = time.time()
            dados = gerar_relatorio()
            dados["tempo_segundos"] = round(time.time() - inicio, 1)
            self._responder(200, dados)
        except Exception as erro:  # noqa: BLE001
            self._responder(500, {"ok": False, "erro": str(erro)})
        finally:
            _lock.release()

    def do_GET(self):
        if self.path.rstrip("/") in ("", "/relatorio"):
            self._gerar()
        else:
            self._responder(404, {"ok": False, "erro": f"Rota não encontrada: {self.path}"})

    def do_POST(self):
        self.do_GET()

    def log_message(self, fmt, *args):
        print(f"[api] {self.address_string()} - {fmt % args}")


def main():
    servidor = ThreadingHTTPServer(("0.0.0.0", PORTA), Handler)
    print(f"API Windy rodando em http://localhost:{PORTA}/relatorio")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando API...")
        servidor.shutdown()


if __name__ == "__main__":
    main()
