import time

from rotalag.config import Config
from rotalag.collector import Coletor
from rotalag.ping import ResultadoPing
from rotalag.report import formatar_perfil, perfil_por_hora, piores_horarios
from rotalag.storage import Banco


def test_grava_e_gera_perfil(tmp_path):
    banco = Banco(tmp_path / "dados.db")
    a = banco.garantir_alvo("8.8.8.8", "publico")
    assert banco.garantir_alvo("8.8.8.8", "publico") == a

    agora = time.time()
    banco.gravar_amostra(a, ResultadoPing("8.8.8.8", 10, 10, (10,) * 10), agora - 60)
    banco.gravar_amostra(a, ResultadoPing("8.8.8.8", 10, 8, (20,) * 8), agora - 30)

    perfil = perfil_por_hora(banco, agora=agora)
    assert len(perfil) == 1
    linha = perfil[0]
    assert linha.amostras == 2
    assert linha.media_ms == 15
    assert linha.perda_pct == 10  # 2 perdidos em 20 enviados
    assert "8.8.8.8" in formatar_perfil(perfil)
    banco.fechar()


def test_perfil_ignora_amostras_antigas(tmp_path):
    banco = Banco(tmp_path / "dados.db")
    a = banco.garantir_alvo("1.1.1.1", "publico")
    agora = time.time()
    banco.gravar_amostra(a, ResultadoPing("1.1.1.1", 1, 1, (5,)), agora - 30 * 86400)
    assert perfil_por_hora(banco, dias=7, agora=agora) == []
    banco.fechar()


def test_piores_horarios_ordena_por_perda():
    from rotalag.report import LinhaPerfil

    perfil = [
        LinhaPerfil(20, "8.8.8.8", 1, 30, 2, 0),
        LinhaPerfil(21, "8.8.8.8", 1, 90, 10, 5),
        LinhaPerfil(22, "8.8.8.8", 1, 40, 3, 1),
    ]
    assert [l.hora for l in piores_horarios(perfil, 2)] == [21, 22]


def test_coletor_grava_rodada_sem_rede(tmp_path):
    banco = Banco(tmp_path / "dados.db")
    config = Config(alvos=["8.8.8.8"], monitorar_gateway=False, banco=tmp_path / "dados.db")
    falso = lambda alvo, n, t: ResultadoPing(alvo, n, n, (12.0,) * n)
    coletor = Coletor(config, banco, funcao_ping=falso)
    alvo_id = banco.garantir_alvo("8.8.8.8", "publico")
    coletor.rodar_uma_vez("8.8.8.8", alvo_id)
    assert coletor.ultimo["8.8.8.8"].media_ms == 12
    assert banco.consultar("SELECT COUNT(*) AS n FROM amostras_ping")[0]["n"] == 1
    banco.fechar()
