from __future__ import annotations

from ..source import Event
from ._etickets_asmx import fetch_grouped_events


class AvalonSource:
    key = "avalon"
    display_name = "avalonbooking.mk"

    API_URL = "https://avalonbooking.mk/services/exportdata.asmx/GetGroupedEvents"
    EVENT_URL = "https://avalonbooking.mk/event-details-mk.nspx?eventid={id}"

    def fetch(self) -> list[Event]:
        return fetch_grouped_events(self.API_URL, self.EVENT_URL)
