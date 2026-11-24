"""Coletor da linha de base: pinga cada alvo em intervalos fixos e grava no banco."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

from .config import Config
from .gateway import descobrir_gateway
from .ping import ResultadoPing, pingar
from .storage import Banco

log = logging.getLogger(__name__)

FuncaoPing = Callable[[str, int, int], ResultadoPing]


class Coletor:
    """Uma thread por alvo. Cada thread roda uma rodada de ping a cada ``intervalo_s``."""

    def __init__(self, config: Config, banco: Banco, funcao_ping: FuncaoPing = pingar) -> None:
        self.config = config
        self.banco = banco
        self._pingar = funcao_ping
        self._parar = threading.Event()
        self._threads: list[threading.Thread] = []
        self.ultimo: dict[str, ResultadoPing] = {}
        """Último resultado por alvo, para mostrar no ícone da bandeja."""

    def alvos(self) -> list[tuple[str, str]]:
        lista = [(a, "publico") for a in self.config.alvos]
        if self.config.monitorar_gateway:
            gw = descobrir_gateway()
            if gw:
                lista.insert(0, (gw, "gateway"))
            else:
                log.warning("Não foi possível descobrir o gateway; seguindo só com os alvos públicos.")
        return lista

    def iniciar(self) -> None:
        for endereco, tipo in self.alvos():
            alvo_id = self.banco.garantir_alvo(endereco, tipo)
            t = threading.Thread(
                target=self._laco, args=(endereco, alvo_id), name=f"ping-{endereco}", daemon=True
            )
            t.start()
            self._threads.append(t)
            log.info("Monitorando %s (%s)", endereco, tipo)

    def parar(self, espera_s: float = 5.0) -> None:
        self._parar.set()
        for t in self._threads:
            t.join(timeout=espera_s)

    def rodar_uma_vez(self, endereco: str, alvo_id: int) -> ResultadoPing:
        r = self._pingar(endereco, self.config.pacotes, self.config.timeout_ms)
        self.banco.gravar_amostra(alvo_id, r)
        self.ultimo[endereco] = r
        log.debug(
            "%s: média %s ms, perda %.0f%%, jitter %s ms",
            endereco, r.media_ms, r.perda_pct, r.jitter_ms,
        )
        return r

    def _laco(self, endereco: str, alvo_id: int) -> None:
        while not self._parar.is_set():
            inicio = time.monotonic()
            try:
                self.rodar_uma_vez(endereco, alvo_id)
            except Exception:  # noqa: BLE001 - o coletor nunca pode morrer por um erro pontual
                log.exception("Falha ao pingar %s", endereco)
            restante = self.config.intervalo_s - (time.monotonic() - inicio)
            if restante > 0:
                self._parar.wait(restante)
