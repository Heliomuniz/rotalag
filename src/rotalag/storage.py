"""Banco SQLite local do RotaLag.

A fase 1 cria só as tabelas da linha de base (``alvos`` e ``amostras_ping``).
As tabelas de rotas, jogos e alertas entram nas fases seguintes.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from .ping import ResultadoPing

VERSAO_ESQUEMA = 1

ESQUEMA = """
CREATE TABLE IF NOT EXISTS alvos (
    id        INTEGER PRIMARY KEY,
    endereco  TEXT NOT NULL UNIQUE,
    tipo      TEXT NOT NULL CHECK (tipo IN ('publico', 'gateway', 'jogo')),
    criado_em REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS amostras_ping (
    id         INTEGER PRIMARY KEY,
    alvo_id    INTEGER NOT NULL REFERENCES alvos(id),
    horario    REAL NOT NULL,          -- segundos desde 1970 (UTC)
    enviados   INTEGER NOT NULL,
    recebidos  INTEGER NOT NULL,
    perda_pct  REAL NOT NULL,
    media_ms   REAL,
    min_ms     REAL,
    max_ms     REAL,
    jitter_ms  REAL
);

CREATE INDEX IF NOT EXISTS idx_amostras_alvo_horario ON amostras_ping (alvo_id, horario);
"""


class Banco:
    """Acesso ao banco. Seguro para uso por várias threads (uma conexão, com trava)."""

    def __init__(self, caminho: Path | str) -> None:
        if str(caminho) != ":memory:":
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(str(caminho), check_same_thread=False)
        self._con.row_factory = sqlite3.Row
        self._trava = threading.Lock()
        with self._trava, self._con:
            self._con.execute("PRAGMA journal_mode=WAL")
            self._con.execute("PRAGMA foreign_keys=ON")
            self._con.executescript(ESQUEMA)
            self._con.execute(f"PRAGMA user_version={VERSAO_ESQUEMA}")

    def fechar(self) -> None:
        with self._trava:
            self._con.close()

    def garantir_alvo(self, endereco: str, tipo: str) -> int:
        """Cadastra o alvo se ainda não existir e devolve o seu id."""
        with self._trava, self._con:
            self._con.execute(
                "INSERT OR IGNORE INTO alvos (endereco, tipo, criado_em) VALUES (?, ?, ?)",
                (endereco, tipo, time.time()),
            )
            linha = self._con.execute(
                "SELECT id FROM alvos WHERE endereco = ?", (endereco,)
            ).fetchone()
        return int(linha["id"])

    def gravar_amostra(self, alvo_id: int, r: ResultadoPing, horario: float | None = None) -> None:
        with self._trava, self._con:
            self._con.execute(
                """INSERT INTO amostras_ping
                   (alvo_id, horario, enviados, recebidos, perda_pct, media_ms, min_ms, max_ms, jitter_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    alvo_id,
                    time.time() if horario is None else horario,
                    r.enviados,
                    r.recebidos,
                    r.perda_pct,
                    r.media_ms,
                    r.min_ms,
                    r.max_ms,
                    r.jitter_ms,
                ),
            )

    def consultar(self, sql: str, parametros: tuple = ()) -> list[sqlite3.Row]:
        with self._trava:
            return self._con.execute(sql, parametros).fetchall()
