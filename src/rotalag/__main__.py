"""Linha de comando do RotaLag.

    python -m rotalag rodar          # inicia o monitoramento (com ícone, se disponível)
    python -m rotalag relatorio      # perfil por hora dos últimos 7 dias
    python -m rotalag testar         # uma rodada de ping em cada alvo, sem gravar
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading

from . import __version__
from .collector import Coletor
from .config import carregar
from .ping import pingar
from .report import formatar_perfil, perfil_por_hora
from .storage import Banco


def _cmd_rodar(args: argparse.Namespace) -> int:
    config = carregar()
    banco = Banco(config.banco)
    coletor = Coletor(config, banco)
    coletor.iniciar()
    logging.info("Gravando em %s. Ctrl+C para sair.", config.banco)

    def sair():
        coletor.parar()
        banco.fechar()

    def mostrar_relatorio():
        texto = formatar_perfil(perfil_por_hora(banco))
        caminho = os.path.join(tempfile.gettempdir(), "rotalag-relatorio.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)
        if sys.platform == "win32":
            os.startfile(caminho)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", caminho])

    if not args.sem_bandeja:
        from .tray import rodar_bandeja

        if rodar_bandeja(coletor, sair, mostrar_relatorio):
            return 0

    fim = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: fim.set())
    signal.signal(signal.SIGTERM, lambda *_: fim.set())
    fim.wait()
    sair()
    return 0


def _cmd_relatorio(args: argparse.Namespace) -> int:
    config = carregar()
    if not config.banco.exists():
        print("Ainda não há banco de dados. Rode 'python -m rotalag rodar' primeiro.")
        return 1
    banco = Banco(config.banco)
    print(formatar_perfil(perfil_por_hora(banco, dias=args.dias)))
    banco.fechar()
    return 0


def _cmd_testar(_args: argparse.Namespace) -> int:
    config = carregar()
    coletor = Coletor(config, banco=None)  # type: ignore[arg-type]
    for endereco, tipo in coletor.alvos():
        r = pingar(endereco, min(config.pacotes, 4), config.timeout_ms)
        media = "-" if r.media_ms is None else f"{r.media_ms:.1f}"
        print(f"{endereco:<16} ({tipo:<7}) média {media} ms, perda {r.perda_pct:.0f}%")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rotalag", description="Monitor de rede para jogos.")
    parser.add_argument("--version", action="version", version=f"rotalag {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="mostra cada medição")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("rodar", help="inicia o monitoramento em segundo plano")
    p.add_argument("--sem-bandeja", action="store_true", help="não mostra o ícone na bandeja")
    p.set_defaults(func=_cmd_rodar)

    p = sub.add_parser("relatorio", help="perfil da conexão por hora do dia")
    p.add_argument("--dias", type=float, default=7, help="quantos dias olhar para trás (padrão 7)")
    p.set_defaults(func=_cmd_relatorio)

    p = sub.add_parser("testar", help="uma rodada rápida de ping em cada alvo, sem gravar")
    p.set_defaults(func=_cmd_testar)

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
