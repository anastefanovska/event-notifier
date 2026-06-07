from __future__ import annotations

import html as html_lib
import re

from .. import dates
from ..http import DEFAULT_TIMEOUT, session
from ..source import Event

PAGE_URL = "https://www.karti.com.mk/"
BASE_URL = "https://www.karti.com.mk"

# Each event on the home page is a single anchor card:
#   <a class="k_event_link ..." href=steve-aoki.nspx title=...>
#     <h2 class="k-event-list-event-title ...">Title</h2>
#     <div class="k-events-event-date">5-12&nbsp;<span class="mm">Јуни</span> ...</div>
#     <div class="k-events-venue-details">Venue</div>
#     <span class="cost">250-700</span> <span class="currency">мкд</span>
#   </a>
# The href is unquoted; the slug is what identifies the event.
EVENT_CARD_RE = re.compile(
    r'<a[^>]*class="[^"]*\bk_event_link\b[^"]*"[^>]*href=([^\s>]+\.nspx)[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
TITLE_RE = re.compile(r'k-event-list-event-title[^"]*">(.*?)</h2>', re.IGNORECASE | re.DOTALL)
DATE_RE = re.compile(r'k-events-event-date">(.*?)</div>', re.IGNORECASE | re.DOTALL)
VENUE_RE = re.compile(r'k-events-venue-details">(.*?)</div>', re.IGNORECASE | re.DOTALL)


def _text(fragment: str | None) -> str | None:
    if fragment is None:
        return None
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = html_lib.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _match(pattern: re.Pattern[str], body: str) -> str | None:
    found = pattern.search(body)
    return _text(found.group(1)) if found else None


def parse_events(html: str) -> list[Event]:
    seen_slugs: set[str] = set()
    events: list[Event] = []
    for match in EVENT_CARD_RE.finditer(html):
        slug = match.group(1).strip("\"' ").lower()
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        body = match.group(2)

        events.append(
            Event(
                id=slug,
                url=f"{BASE_URL}/{slug}",
                title=_match(TITLE_RE, body),
                date=dates.from_named(_match(DATE_RE, body)),
                venue=_match(VENUE_RE, body),
            )
        )
    return events


class KartiSource:
    key = "karti"
    display_name = "karti.com.mk"

    def fetch(self) -> list[Event]:
        with session() as s:
            response = s.get(PAGE_URL, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            html = response.text
        return parse_events(html)
