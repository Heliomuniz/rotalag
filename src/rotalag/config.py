"""Configuração do RotaLag.

Os valores padrão funcionam sem nenhum arquivo. Para mudar algo, crie
``config.toml`` na pasta de dados (veja ``pasta_dados``) com, por exemplo::

    intervalo_s = 30
    pacotes = 10
    alvos = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]
    monitorar_gateway = true
"""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

ALVOS_PADRAO = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]


def pasta_dados() -> Path:
    """Pasta onde ficam o banco e a configuração."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "RotaLag"


@dataclass
class Config:
    intervalo_s: int = 30
    """Segundos entre o início de duas rodadas de ping para o mesmo alvo."""

    pacotes: int = 10
    """Pacotes enviados por rodada (o ping manda cerca de 1 por segundo)."""

    timeout_ms: int = 1000
    """Tempo máximo de espera por resposta de cada pacote."""

    alvos: list[str] = field(default_factory=lambda: list(ALVOS_PADRAO))
    """Alvos públicos de referência."""

    monitorar_gateway: bool = True
    """Também pinga o roteador/modem, para separar problema da rede de casa do provedor."""

    banco: Path = field(default_factory=lambda: pasta_dados() / "dados.db")

    def __post_init__(self) -> None:
        if self.intervalo_s < 1:
            raise ValueError("intervalo_s deve ser pelo menos 1")
        if self.pacotes < 1:
            raise ValueError("pacotes deve ser pelo menos 1")
        self.banco = Path(self.banco)


def carregar(caminho: Path | None = None) -> Config:
    """Lê ``config.toml`` se existir; senão usa os padrões."""
    caminho = caminho or pasta_dados() / "config.toml"
    if not caminho.exists():
        return Config()
    with caminho.open("rb") as f:
        dados = tomllib.load(f)
    conhecidos = {f.name for f in fields(Config)}
    desconhecidos = set(dados) - conhecidos
    if desconhecidos:
        raise ValueError(f"Chaves desconhecidas em {caminho}: {', '.join(sorted(desconhecidos))}")
    return Config(**dados)
