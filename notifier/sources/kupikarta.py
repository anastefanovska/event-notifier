from __future__ import annotations

from ..source import Event
from ._etickets_asmx import fetch_grouped_events


class KupiKartaSource:
    key = "kupikarta"
    display_name = "kupikarta.com"

    API_URL = "https://kupikarta.com/services/exportdata.asmx/GetGroupedEvents"
    EVENT_URL = "https://kupikarta.com/tickets.nspx?eventid={id}"
    IMAGE_BASE = "https://kupikarta.com"

    def fetch(self) -> list[Event]:
        return fetch_grouped_events(self.API_URL, self.EVENT_URL, self.IMAGE_BASE)
