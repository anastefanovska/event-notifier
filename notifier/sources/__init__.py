from ..source import Source
from .avalon import AvalonSource
from .karti import KartiSource
from .kupikarta import KupiKartaSource
from .mktickets import MkTicketsSource
from .ticketx import TicketXSource

ALL_SOURCES: list[Source] = [
    AvalonSource(),
    KupiKartaSource(),
    KartiSource(),
    MkTicketsSource(),
    TicketXSource(),
]

__all__ = [
    "ALL_SOURCES",
    "AvalonSource",
    "KartiSource",
    "KupiKartaSource",
    "MkTicketsSource",
    "TicketXSource",
]
