
from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path
import base64
import os

# =====================================================
# CONFIGURAÇÕES
# =====================================================

URL = "https://www.windy.com/-22.264/-49.136?-22.548,-49.136,9"

# Salva na mesma pasta em que está o script
PASTA = Path(__file__).resolve().parent / "prints_windy"
PASTA.mkdir(parents=True, exist_ok=True)

LARGURA = 1848
ALTURA = 832

# Variáveis de ambiente (usadas pela api.py / n8n)
TEMPO_CARREGAMENTO = int(os.environ.get("CLIMA_WAIT_MS", "15000"))  # ms
HEADLESS = os.environ.get("CLIMA_HEADLESS", "1") != "0"  # CLIMA_HEADLESS=0 abre a janela


# =====================================================
# NÚCLEO
# =====================================================

def gerar_relatorio(url=URL, headless=HEADLESS, wait_ms=TEMPO_CARREGAMENTO,
                    salvar=True, apenas_texto=False):
    """Executa o scraper do Windy e devolve um dicionário com o relatório.

    Retorna:
        {
          "ok": bool,
          "local": str,
          "data": "YYYY-MM-DD",
          "horario": "HH:MM:SS",
          "url": str,
          "resumo": str,        # mensagem curta, ideal para WhatsApp
          "texto": str,         # relatório completo extraído da página
          "imagem_base64": str, # só se apenas_texto=False
          "arquivo_print": str | None,
          "arquivo_texto": str | None,
        }
    """
    agora = datetime.now()
    identificador = agora.strftime("%Y-%m-%d_%H-%M-%S")

    arquivo_print = PASTA / f"windy_bauru_{identificador}.png"
    arquivo_texto = PASTA / f"windy_dados_{identificador}.txt"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            context = browser.new_context(
                viewport={"width": LARGURA, "height": ALTURA},
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
                device_scale_factor=1,
            )
            page = context.new_page()

            print("[1/4] Abrindo Windy...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            print("[2/4] Aguardando mapa e previsões...")
            page.wait_for_timeout(wait_ms)

            print("[3/4] Capturando imagem...")
            png_bytes = page.screenshot(full_page=False, timeout=30000)

            print("[4/4] Extraindo informações da página...")
            try:
                texto_bruto = page.locator("body").inner_text(timeout=15000)
                linhas = [l.strip() for l in texto_bruto.splitlines() if l.strip()]
                texto = "\n".join(linhas)
            except Exception as erro:
                texto = f"Não foi possível extrair os textos.\nErro: {erro}"
        finally:
            browser.close()

    relatorio = f"""
=======================================================
RELATÓRIO METEOROLÓGICO - WINDY
=======================================================

LOCAL: Bauru/SP e região
DATA: {agora.strftime('%d/%m/%Y')}
HORÁRIO: {agora.strftime('%H:%M:%S')}

FONTE:
{url}

=======================================================
INFORMAÇÕES EXTRAÍDAS DA PÁGINA
=======================================================

{texto if texto else 'Nenhum texto disponível para extração.'}

=======================================================
FIM DO RELATÓRIO
=======================================================
""".strip()

    resultado = {
        "ok": True,
        "local": "Bauru/SP e região",
        "data": agora.strftime("%Y-%m-%d"),
        "horario": agora.strftime("%H:%M:%S"),
        "url": url,
        "resumo": montar_resumo(agora, texto),
        "texto": relatorio,
        "imagem_base64": None if apenas_texto else base64.b64encode(png_bytes).decode(),
        "arquivo_print": None,
        "arquivo_texto": None,
    }

    if salvar:
        arquivo_print.write_bytes(png_bytes)
        arquivo_texto.write_text(relatorio, encoding="utf-8")
        resultado["arquivo_print"] = str(arquivo_print)
        resultado["arquivo_texto"] = str(arquivo_texto)
        print(f"Print salvo: {arquivo_print}")
        print(f"Relatório salvo: {arquivo_texto}")

    return resultado


def montar_resumo(agora, texto):
    """Monta uma mensagem curta e legível para WhatsApp."""
    linhas = texto.splitlines()

    # Temperaturas de hoje: a primeira linha que começa com graus (ex: "24°\t21°\t...")
    temps_hoje = ""
    for i, linha in enumerate(linhas):
        if linha.startswith(("0°", "1°", "2°", "3°")) or (
            linha[:2].rstrip("°").isdigit() and "°" in linha[:4] and "\t" in linha
        ):
            valores = [v for v in linha.split("\t") if v][:8]
            if len(valores) >= 4:
                horas = ["0h", "3h", "6h", "9h", "12h", "15h", "18h", "21h"]
                temps_hoje = "  ".join(f"{h}: {v}" for h, v in zip(horas, valores))
                break

    # Previsibilidade dos próximos dias:
    # linhas na ordem: "Quinta-feira 12" / "50%" / "previsibilidade"
    previsibilidade = []
    for i, linha in enumerate(linhas):
        if "previsibilidade" in linha and i >= 2:
            pct = linhas[i - 1]
            dia = linhas[i - 2]
            if pct.endswith("%") and not dia.endswith("%"):
                previsibilidade.append(f"• {dia}: {pct}")
        if len(previsibilidade) >= 4:
            break

    partes = [
        "🌤 *RELATÓRIO WINDY — Bauru/SP*",
        f"📅 {agora.strftime('%d/%m/%Y')} às {agora.strftime('%H:%M')}",
        "",
    ]
    if temps_hoje:
        partes += ["🌡 *Temperatura hoje (°C)*", temps_hoje, ""]
    if previsibilidade:
        partes += ["📊 *Previsibilidade*", *previsibilidade, ""]
    partes += ["🖼️ Print do mapa em anexo", "🔗 windy.com"]

    return "\n".join(partes)


# =====================================================
# CLI (mantém o comportamento original: python print.py)
# =====================================================

def executar():
    print("=" * 55)
    print("ROBÔ DE MONITORAMENTO METEOROLÓGICO")
    print("=" * 55)

    resultado = gerar_relatorio()

    print("\n" + "=" * 55)
    print("PROCESSO FINALIZADO COM SUCESSO")
    print("=" * 55)
    print(f"\nPasta de saída: {PASTA}")
    print(f"Imagem: {Path(resultado['arquivo_print']).name}")
    print(f"Texto: {Path(resultado['arquivo_texto']).name}")


if __name__ == "__main__":
    executar()
