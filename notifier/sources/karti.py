from __future__ import annotations

import re

from ..http import DEFAULT_TIMEOUT, session
from ..source import Event

PAGE_URL = "https://www.karti.com.mk/"

# Event cards on the home page are anchored as:
#   <a class="k_event_link col-xs-12 col-md-4 mix concerts other" href=steve-aoki.nspx ...>
# The href is unquoted; the slug is what identifies the event.
EVENT_LINK_RE = re.compile(
    r'<a[^>]*class="[^"]*\bk_event_link\b[^"]*"[^>]*href=([^\s>]+\.nspx)',
    re.IGNORECASE,
)


class KartiSource:
    key = "karti"
    display_name = "karti.com.mk"

    def fetch(self) -> list[Event]:
        with session() as s:
            response = s.get(PAGE_URL, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            html = response.text

        seen_slugs: set[str] = set()
        events: list[Event] = []
        for match in EVENT_LINK_RE.finditer(html):
            slug = match.group(1).strip('"\' ').lower()
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            events.append(Event(id=slug, url=f"https://www.karti.com.mk/{slug}"))
        return events
