from rotalag.gateway import gateway_da_saida_ip_route, gateway_da_saida_route_print

ROUTE_PRINT = """
IPv4 Tabela de rota
===========================================================================
Rotas ativas:
Endereço de rede             Máscara     Ender. gateway    Interface  Custo
          0.0.0.0          0.0.0.0      192.168.0.1    192.168.0.15     25
        127.0.0.0        255.0.0.0         No vínculo         127.0.0.1    331
"""


def test_windows():
    assert gateway_da_saida_route_print(ROUTE_PRINT) == "192.168.0.1"


def test_windows_sem_rota_padrao():
    assert gateway_da_saida_route_print("nada aqui") is None


def test_linux():
    assert gateway_da_saida_ip_route("default via 10.0.0.1 dev eth0 proto dhcp") == "10.0.0.1"
