from __future__ import annotations

import re

from ..http import DEFAULT_TIMEOUT, session
from ..source import Event

PAGE_URL = "https://ticketx.com.mk/"
BASE_URL = "https://ticketx.com.mk"

EVENT_LINK_RE = re.compile(r'href="(/events/[a-z0-9-]+)"', re.IGNORECASE)


class TicketXSource:
    key = "ticketx"
    display_name = "ticketx.com.mk"

    def fetch(self) -> list[Event]:
        with session() as s:
            response = s.get(PAGE_URL, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            html = response.text

        seen_paths: set[str] = set()
        events: list[Event] = []
        for match in EVENT_LINK_RE.finditer(html):
            path = match.group(1)
            if path in seen_paths:
                continue
            seen_paths.add(path)
            slug = path.rsplit("/", 1)[-1]
            events.append(Event(id=slug, url=f"{BASE_URL}{path}"))
        return events
