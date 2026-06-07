from __future__ import annotations

import html as html_lib
import re

from .. import dates
from ..http import DEFAULT_TIMEOUT, session
from ..source import Event

PAGE_URL = "https://mktickets.mk/"

# Each event on the home page is rendered as:
#   <div class="event-container">
#     <a href="https://mktickets.mk/event/<slug>/" class="poster-link">...</a>
#     <div class="event-hover">
#     <h3><a href=".../event/<slug>/">Title</a></h3>
#     <p> <span> City, , </span> <span>26-06-2026</span>
EVENT_CARD_RE = re.compile(
    r'<div class="event-container">(.*?)<h3>\s*<a[^>]*href="(https://mktickets\.mk/event/[a-z0-9-]+/?)"[^>]*>(.*?)</a>\s*</h3>(.*?)(?=<div class="event-container">|$)',
    re.IGNORECASE | re.DOTALL,
)
SPAN_RE = re.compile(r"<span>(.*?)</span>", re.IGNORECASE | re.DOTALL)


def _text(fragment: str | None) -> str | None:
    if fragment is None:
        return None
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = html_lib.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _venue(spans: list[str]) -> str | None:
    for span in spans:
        text = _text(span)
        if text and not dates.from_numeric(text):
            return text.strip(" ,")
    return None


def _date(spans: list[str]) -> str | None:
    for span in spans:
        found = dates.from_numeric(_text(span))
        if found:
            return found
    return None


def parse_events(html: str) -> list[Event]:
    seen_urls: set[str] = set()
    events: list[Event] = []
    for match in EVENT_CARD_RE.finditer(html):
        url = match.group(2).rstrip("/") + "/"
        if url in seen_urls:
            continue
        seen_urls.add(url)
        slug = url.rsplit("/event/", 1)[-1].strip("/")
        spans = SPAN_RE.findall(match.group(4))
        events.append(
            Event(
                id=slug,
                url=url,
                title=_text(match.group(3)),
                date=_date(spans),
                venue=_venue(spans),
            )
        )
    return events


class MkTicketsSource:
    key = "mktickets"
    display_name = "mktickets.mk"

    def fetch(self) -> list[Event]:
        with session() as s:
            response = s.get(PAGE_URL, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            html = response.text
        return parse_events(html)
