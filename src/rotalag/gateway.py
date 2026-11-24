"""Descobre o gateway padrão (o roteador/modem da casa)."""

from __future__ import annotations

import ipaddress
import re
import subprocess
import sys

_RE_IPV4 = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")


def _ipv4_valido(texto: str) -> bool:
    try:
        ip = ipaddress.IPv4Address(texto)
    except ValueError:
        return False
    return not ip.is_unspecified


def gateway_da_saida_route_print(saida: str) -> str | None:
    """Lê a rota padrão (0.0.0.0/0.0.0.0) da saída de ``route print -4`` do Windows."""
    for linha in saida.splitlines():
        partes = linha.split()
        if len(partes) >= 3 and partes[0] == "0.0.0.0" and partes[1] == "0.0.0.0":
            if _ipv4_valido(partes[2]):
                return partes[2]
    return None


def gateway_da_saida_ip_route(saida: str) -> str | None:
    """Lê a rota padrão da saída de ``ip route show default`` do Linux."""
    m = re.search(r"default via (\S+)", saida)
    if m and _ipv4_valido(m.group(1)):
        return m.group(1)
    return None


def descobrir_gateway() -> str | None:
    """Devolve o IP do gateway padrão, ou ``None`` se não for possível descobrir."""
    try:
        if sys.platform == "win32":
            saida = subprocess.run(
                ["route", "print", "-4"],
                capture_output=True,
                text=True,
                errors="replace",
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
            ).stdout
            return gateway_da_saida_route_print(saida)
        saida = subprocess.run(
            ["ip", "route", "show", "default"], capture_output=True, text=True, timeout=10
        ).stdout
        return gateway_da_saida_ip_route(saida)
    except (OSError, subprocess.TimeoutExpired):
        return None
