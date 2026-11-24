"""Ícone na bandeja do sistema (opcional: precisa de ``pip install rotalag[bandeja]``)."""

from __future__ import annotations

import logging
import threading

from .collector import Coletor

log = logging.getLogger(__name__)

# Cores do ícone por estado da conexão.
VERDE = (46, 160, 67)
AMARELO = (210, 153, 34)
VERMELHO = (207, 34, 46)
CINZA = (130, 130, 130)


def estado(coletor: Coletor) -> tuple[tuple[int, int, int], str]:
    """Cor e texto do ícone, a partir do último resultado de cada alvo público."""
    publicos = [coletor.ultimo[a] for a in coletor.config.alvos if a in coletor.ultimo]
    if not publicos:
        return CINZA, "RotaLag: aguardando a primeira medição"
    perda = max(r.perda_pct for r in publicos)
    medias = [r.media_ms for r in publicos if r.media_ms is not None]
    media = sum(medias) / len(medias) if medias else None
    texto = f"RotaLag: perda {perda:.0f}%" + (f", média {media:.0f} ms" if media is not None else "")
    if perda >= 5 or media is None:
        return VERMELHO, texto
    if perda > 0 or media > 100:
        return AMARELO, texto
    return VERDE, texto


def _imagem(cor: tuple[int, int, int]):
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((6, 6, 58, 58), fill=cor)
    return img


def rodar_bandeja(coletor: Coletor, ao_sair, mostrar_relatorio) -> bool:
    """Mostra o ícone e bloqueia até o usuário escolher Sair.

    Devolve ``False`` se as bibliotecas da bandeja não estiverem instaladas.
    """
    try:
        import pystray
    except ImportError:
        log.info("pystray não instalado; rodando sem ícone na bandeja.")
        return False

    parar = threading.Event()

    def sair(icone, _item):
        parar.set()
        ao_sair()
        icone.stop()

    icone = pystray.Icon(
        "rotalag",
        _imagem(CINZA),
        "RotaLag",
        menu=pystray.Menu(
            pystray.MenuItem("Ver relatório por hora", lambda *_: mostrar_relatorio()),
            pystray.MenuItem("Sair", sair),
        ),
    )

    def atualizar():
        while not parar.wait(5):
            cor, texto = estado(coletor)
            icone.icon = _imagem(cor)
            icone.title = texto

    threading.Thread(target=atualizar, daemon=True).start()
    icone.run()
    return True
