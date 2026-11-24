"""Ping usando o comando do sistema (não precisa de administrador).

Funciona com a saída do ``ping`` do Windows em português e em inglês, e do
``ping`` do Linux/macOS.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from statistics import mean

# "tempo=12ms", "tempo<1ms", "time=12ms", "time=12.3 ms", "tempo=12,3 ms"
_RE_TEMPO = re.compile(r"(?:time|tempo)\s*([=<])\s*(\d+(?:[.,]\d+)?)\s*ms", re.IGNORECASE)


@dataclass(frozen=True)
class ResultadoPing:
    alvo: str
    enviados: int
    recebidos: int
    rtts_ms: tuple[float, ...]

    @property
    def perda_pct(self) -> float:
        if self.enviados == 0:
            return 100.0
        return 100.0 * (self.enviados - self.recebidos) / self.enviados

    @property
    def media_ms(self) -> float | None:
        return mean(self.rtts_ms) if self.rtts_ms else None

    @property
    def min_ms(self) -> float | None:
        return min(self.rtts_ms) if self.rtts_ms else None

    @property
    def max_ms(self) -> float | None:
        return max(self.rtts_ms) if self.rtts_ms else None

    @property
    def jitter_ms(self) -> float | None:
        """Média da variação absoluta entre respostas seguidas."""
        if len(self.rtts_ms) < 2:
            return None
        difs = [abs(b - a) for a, b in zip(self.rtts_ms, self.rtts_ms[1:])]
        return mean(difs)


def extrair_rtts(saida: str) -> list[float]:
    """Extrai os tempos de resposta (ms) da saída do ping, na ordem."""
    rtts = []
    for sinal, valor in _RE_TEMPO.findall(saida):
        v = float(valor.replace(",", "."))
        # "tempo<1ms" no Windows: registramos meio milissegundo.
        rtts.append(v / 2 if sinal == "<" else v)
    return rtts


def montar_comando(alvo: str, pacotes: int, timeout_ms: int) -> list[str]:
    if sys.platform == "win32":
        return ["ping", "-n", str(pacotes), "-w", str(timeout_ms), alvo]
    timeout_s = max(1, round(timeout_ms / 1000))
    return ["ping", "-n", "-c", str(pacotes), "-W", str(timeout_s), alvo]


def pingar(alvo: str, pacotes: int = 10, timeout_ms: int = 1000) -> ResultadoPing:
    """Executa uma rodada de ping e devolve as estatísticas."""
    cmd = montar_comando(alvo, pacotes, timeout_ms)
    criacao = {}
    if sys.platform == "win32":
        # Evita abrir uma janela de console a cada ping.
        criacao["creationflags"] = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    limite = pacotes * (timeout_ms / 1000 + 1) + 5
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=limite,
            **criacao,
        )
        saida = proc.stdout
    except FileNotFoundError as e:
        # Sem o comando ping não dá para medir; isso não é perda de pacotes.
        raise RuntimeError("Comando 'ping' não encontrado neste sistema") from e
    except subprocess.TimeoutExpired:
        saida = ""
    rtts = extrair_rtts(saida)[:pacotes]
    return ResultadoPing(alvo=alvo, enviados=pacotes, recebidos=len(rtts), rtts_ms=tuple(rtts))
