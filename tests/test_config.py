import pytest

from rotalag.config import Config, carregar


def test_padrao_sem_arquivo(tmp_path):
    c = carregar(tmp_path / "nao-existe.toml")
    assert "8.8.8.8" in c.alvos and c.intervalo_s == 30


def test_le_arquivo(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text('intervalo_s = 60\nalvos = ["1.1.1.1"]\n', encoding="utf-8")
    c = carregar(p)
    assert c.intervalo_s == 60 and c.alvos == ["1.1.1.1"]


def test_chave_desconhecida(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text("intervalo = 60\n", encoding="utf-8")
    with pytest.raises(ValueError, match="intervalo"):
        carregar(p)


def test_valida_intervalo():
    with pytest.raises(ValueError):
        Config(intervalo_s=0)
