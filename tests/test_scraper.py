"""Testes do scraper (partes puras: montagem do resumo) — sem internet/navegador."""
from datetime import datetime

from scraper import montar_resumo

AGORA = datetime(2026, 11, 16, 8, 30)

CORPO = """\
Bauru/SP e região
Quinta-feira 13
24°	21°	20°	19°	22°	25°	26°	24°
Sexta-feira 14
60%
previsibilidade
Sábado 15
80%
previsibilidade
"""


def test_resumo_com_temperaturas_positivas():
    resumo = montar_resumo(AGORA, CORPO)
    assert "Temperatura hoje" in resumo
    assert "0h: 24°" in resumo
    assert "21h: 24°" in resumo


def test_resumo_com_temperaturas_negativas():
    """Regressão: cidades frias (-3°) antigamente eram ignoradas pelo parser."""
    corpo = CORPO.replace("24°\t21°", "-3°\t-5°", 1)
    resumo = montar_resumo(AGORA, corpo)
    assert "Temperatura hoje" in resumo
    assert "0h: -3°" in resumo


def test_resumo_sem_linha_de_temperatura():
    corpo = "\n".join(linha for linha in CORPO.splitlines() if "°" not in linha)
    resumo = montar_resumo(AGORA, corpo)
    assert "Temperatura hoje" not in resumo
    # o resto continua de pé
    assert "previsibilidade" in resumo or "Sexta-feira 14: 60%" in resumo


def test_linha_que_nao_e_temperatura_e_ignorada():
    corpo = "Agora	24°	21°\nSexta-feira 14\n60%\nprevisibilidade"
    resumo = montar_resumo(AGORA, corpo)
    assert "Temperatura hoje" not in resumo


def test_previsibilidade_extraida():
    resumo = montar_resumo(AGORA, CORPO)
    assert "• Sexta-feira 14: 60%" in resumo
    assert "• Sábado 15: 80%" in resumo


def test_local_customizado_no_cabecalho():
    resumo = montar_resumo(AGORA, CORPO, local="Marabá/PA")
    assert "RELATÓRIO WINDY — Marabá/PA" in resumo


def test_data_e_hora_no_resumo():
    resumo = montar_resumo(AGORA, CORPO)
    assert "16/11/2026" in resumo
    assert "08:30" in resumo
