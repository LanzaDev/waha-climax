"""Testes do config.py: leitura do .env, validação de chatId e coordenadas."""
import pytest

from config import (
    ConfigError,
    carregar_env,
    obter,
    obter_coordenadas,
    obter_destinatario,
    obter_int,
)

# ---------- carregar_env ----------

def test_carregar_env_lê_chaves_e_ignora_comentários(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(
        "# comentário\n"
        "\n"
        'CHAVE_COMASPAS="valor com espaço"\n'
        "CHAVE_SEM= simples \n"
        "CHAVE_COM_IGUAL=a=b=c\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("CHAVE_COMASPAS", raising=False)
    monkeypatch.delenv("CHAVE_SEM", raising=False)
    monkeypatch.delenv("CHAVE_COM_IGUAL", raising=False)

    assert carregar_env(env) is True
    import os
    assert os.environ["CHAVE_COMASPAS"] == "valor com espaço"
    assert os.environ["CHAVE_SEM"] == "simples"
    assert os.environ["CHAVE_COM_IGUAL"] == "a=b=c"


def test_carregar_env_nao_sobrescreve_variavel_existente(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("MINHA_CHAVE=do_arquivo\n", encoding="utf-8")
    monkeypatch.setenv("MINHA_CHAVE", "do_terminal")

    assert carregar_env(env) is True
    import os
    assert os.environ["MINHA_CHAVE"] == "do_terminal"


def test_carregar_env_arquivo_inexistente(tmp_path):
    assert carregar_env(tmp_path / "nao_existe.env") is False


# ---------- obter / obter_int ----------

def test_obter_obrigatorio_ausente_levanta_erro(monkeypatch):
    monkeypatch.delenv("CHAVE_QUALQUER", raising=False)
    with pytest.raises(ConfigError, match="CHAVE_QUALQUER"):
        obter("CHAVE_QUALQUER", obrigatorio=True)


def test_obter_int_valor_invalido_cai_no_padrao(monkeypatch, capsys):
    monkeypatch.setenv("CLIMA_TESTE_INT", "abc")
    assert obter_int("CLIMA_TESTE_INT", 15000) == 15000
    assert "aviso" in capsys.readouterr().out.lower()


def test_obter_int_vazio_cai_no_padrao(monkeypatch):
    monkeypatch.setenv("CLIMA_TESTE_INT", "  ")
    assert obter_int("CLIMA_TESTE_INT", 8000) == 8000


# ---------- coordenadas ----------

def test_coordenadas_validas(monkeypatch):
    monkeypatch.setenv("CLIMA_LAT", "-22.264")
    monkeypatch.setenv("CLIMA_LON", "-49.136")
    assert obter_coordenadas() == ("-22.264", "-49.136")


def test_coordenadas_com_virgula_decimal(monkeypatch):
    monkeypatch.setenv("CLIMA_LAT", "-22,264")
    monkeypatch.setenv("CLIMA_LON", "-49,136")
    assert obter_coordenadas() == ("-22.264", "-49.136")


def test_coordenadas_texto_invalido(monkeypatch):
    monkeypatch.setenv("CLIMA_LAT", "abc")
    monkeypatch.setenv("CLIMA_LON", "-49.136")
    with pytest.raises(ConfigError, match="inválidos"):
        obter_coordenadas()


def test_coordenadas_fora_do_intervalo(monkeypatch):
    monkeypatch.setenv("CLIMA_LAT", "91")
    monkeypatch.setenv("CLIMA_LON", "-49.136")
    with pytest.raises(ConfigError, match="intervalo"):
        obter_coordenadas()


# ---------- destinatário ----------

def test_destinatario_valido(monkeypatch):
    monkeypatch.setenv("WHATSAPP_CHAT_ID", "5514999999999@c.us")
    monkeypatch.setenv("WAHA_SESSION", "session_abc123")
    assert obter_destinatario() == ("5514999999999@c.us", "session_abc123")


def test_destinatario_chat_invalido(monkeypatch):
    monkeypatch.setenv("WHATSAPP_CHAT_ID", "1499922285")
    monkeypatch.setenv("WAHA_SESSION", "session_abc123")
    with pytest.raises(ConfigError, match="WHATSAPP_CHAT_ID inválido"):
        obter_destinatario()


def test_destinatario_placeholder_do_exemplo(monkeypatch):
    monkeypatch.setenv("WHATSAPP_CHAT_ID", "SEU_NUMERO_AQUI@c.us")
    monkeypatch.setenv("WAHA_SESSION", "session_abc123")
    with pytest.raises(ConfigError, match="Placeholder"):
        obter_destinatario()


def test_destinatario_sessao_com_caractere_invalido(monkeypatch):
    monkeypatch.setenv("WHATSAPP_CHAT_ID", "5514999999999@c.us")
    monkeypatch.setenv("WAHA_SESSION", "sessão com espaço")
    with pytest.raises(ConfigError, match="WAHA_SESSION inválido"):
        obter_destinatario()


def test_destinatario_aceita_grupo(monkeypatch):
    monkeypatch.setenv("WHATSAPP_CHAT_ID", "120363012345678901@g.us")
    monkeypatch.setenv("WAHA_SESSION", "session_abc123")
    assert obter_destinatario()[0].endswith("@g.us")
