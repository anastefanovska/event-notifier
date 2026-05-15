from __future__ import annotations

import re

from ..http import DEFAULT_TIMEOUT, session
from ..source import Event

PAGE_URL = "https://mktickets.mk/"

EVENT_LINK_RE = re.compile(
    r'href="(https://mktickets\.mk/event/[a-z0-9-]+/?)"',
    re.IGNORECASE,
)


class MkTicketsSource:
    key = "mktickets"
    display_name = "mktickets.mk"

    def fetch(self) -> list[Event]:
        with session() as s:
            response = s.get(PAGE_URL, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            html = response.text

        seen_urls: set[str] = set()
        events: list[Event] = []
        for match in EVENT_LINK_RE.finditer(html):
            url = match.group(1).rstrip("/") + "/"
            if url in seen_urls:
                continue
            seen_urls.add(url)
            slug = url.rsplit("/event/", 1)[-1].strip("/")
            events.append(Event(id=slug, url=url))
        return events
