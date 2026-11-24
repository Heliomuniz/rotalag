"""Relatórios a partir do banco: perfil da conexão por hora do dia."""

from __future__ import annotations

import time
from dataclasses import dataclass

from .storage import Banco


@dataclass(frozen=True)
class LinhaPerfil:
    hora: int
    alvo: str
    amostras: int
    media_ms: float | None
    jitter_ms: float | None
    perda_pct: float


def perfil_por_hora(banco: Banco, dias: float = 7, agora: float | None = None) -> list[LinhaPerfil]:
    """Latência, jitter e perda médios por hora do dia (horário local) e por alvo."""
    agora = time.time() if agora is None else agora
    desde = agora - dias * 86400
    linhas = banco.consultar(
        """
        SELECT CAST(strftime('%H', a.horario, 'unixepoch', 'localtime') AS INTEGER) AS hora,
               t.endereco AS alvo,
               COUNT(*) AS amostras,
               AVG(a.media_ms) AS media_ms,
               AVG(a.jitter_ms) AS jitter_ms,
               100.0 * SUM(a.enviados - a.recebidos) / SUM(a.enviados) AS perda_pct
        FROM amostras_ping a JOIN alvos t ON t.id = a.alvo_id
        WHERE a.horario >= ?
        GROUP BY hora, t.endereco
        ORDER BY hora, t.endereco
        """,
        (desde,),
    )
    return [
        LinhaPerfil(
            hora=r["hora"],
            alvo=r["alvo"],
            amostras=r["amostras"],
            media_ms=r["media_ms"],
            jitter_ms=r["jitter_ms"],
            perda_pct=r["perda_pct"] or 0.0,
        )
        for r in linhas
    ]


def piores_horarios(perfil: list[LinhaPerfil], n: int = 3) -> list[LinhaPerfil]:
    """As ``n`` combinações hora/alvo com mais perda; empate decidido pela maior latência."""
    return sorted(perfil, key=lambda l: (l.perda_pct, l.media_ms or 0.0), reverse=True)[:n]


def _fmt(v: float | None, casas: int = 1) -> str:
    return "-" if v is None else f"{v:.{casas}f}"


def formatar_perfil(perfil: list[LinhaPerfil]) -> str:
    if not perfil:
        return "Ainda não há amostras. Deixe o RotaLag rodando por algumas horas."
    cab = f"{'Hora':>4}  {'Alvo':<16} {'Amostras':>8} {'Média ms':>9} {'Jitter ms':>9} {'Perda %':>8}"
    linhas = [cab, "-" * len(cab)]
    for l in perfil:
        linhas.append(
            f"{l.hora:>2}h   {l.alvo:<16} {l.amostras:>8} {_fmt(l.media_ms):>9} "
            f"{_fmt(l.jitter_ms):>9} {_fmt(l.perda_pct):>8}"
        )
    piores = piores_horarios(perfil)
    linhas.append("")
    linhas.append("Horários com mais problemas:")
    for l in piores:
        linhas.append(
            f"  {l.hora:02d}h, {l.alvo}: perda {_fmt(l.perda_pct)}%, média {_fmt(l.media_ms)} ms"
        )
    return "\n".join(linhas)
