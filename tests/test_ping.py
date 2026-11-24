from rotalag.ping import ResultadoPing, extrair_rtts

WINDOWS_PT = """
Disparando 8.8.8.8 com 32 bytes de dados:
Resposta de 8.8.8.8: bytes=32 tempo=14ms TTL=117
Resposta de 8.8.8.8: bytes=32 tempo=18ms TTL=117
Esgotado o tempo limite do pedido.
Resposta de 8.8.8.8: bytes=32 tempo=12ms TTL=117

Estatísticas do Ping para 8.8.8.8:
    Pacotes: Enviados = 4, Recebidos = 3, Perdidos = 1 (25% de perda),
Aproximar um número redondo de vezes em milissegundos:
    Mínimo = 12ms, Máximo = 18ms, Média = 14ms
"""

WINDOWS_EN_GATEWAY = """
Reply from 192.168.0.1: bytes=32 time<1ms TTL=64
Reply from 192.168.0.1: bytes=32 time=2ms TTL=64
"""

WINDOWS_INALCANCAVEL = """
Resposta de 192.168.0.10: Host de destino inacessível.
Resposta de 192.168.0.10: Host de destino inacessível.
"""

LINUX = """
PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.
64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=10.4 ms
64 bytes from 1.1.1.1: icmp_seq=2 ttl=57 time=11.6 ms

--- 1.1.1.1 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1001ms
rtt min/avg/max/mdev = 10.400/11.000/11.600/0.600 ms
"""


def test_windows_portugues():
    assert extrair_rtts(WINDOWS_PT) == [14, 18, 12]


def test_windows_ingles_menor_que_1ms():
    assert extrair_rtts(WINDOWS_EN_GATEWAY) == [0.5, 2]


def test_inalcancavel_nao_conta_como_resposta():
    assert extrair_rtts(WINDOWS_INALCANCAVEL) == []


def test_linux_ignora_linha_de_resumo():
    assert extrair_rtts(LINUX) == [10.4, 11.6]


def test_estatisticas():
    r = ResultadoPing("8.8.8.8", enviados=4, recebidos=3, rtts_ms=(14, 18, 12))
    assert r.perda_pct == 25
    assert r.media_ms == 44 / 3
    assert r.min_ms == 12 and r.max_ms == 18
    assert r.jitter_ms == 5  # (|18-14| + |12-18|) / 2


def test_sem_respostas():
    r = ResultadoPing("x", enviados=4, recebidos=0, rtts_ms=())
    assert r.perda_pct == 100
    assert r.media_ms is None and r.jitter_ms is None
