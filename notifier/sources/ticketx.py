from __future__ import annotations

import json
import re

from .. import dates
from ..source import Event
from ..http import DEFAULT_TIMEOUT, session

PAGE_URL = "https://ticketx.com.mk/"
BASE_URL = "https://ticketx.com.mk"

# ticketx.com.mk is a Next.js app; the home page embeds the full event list as
# JSON in the __NEXT_DATA__ script tag, grouped into sliders/sections.
NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
# Fallback for older markup: plain anchors to event pages.
EVENT_LINK_RE = re.compile(r'href="(/events/[a-z0-9-]+)"', re.IGNORECASE)


def _clean(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


# ticketx titles often append the event date, e.g. "2БОНА - ВЕЛЕС - 15.05.2026".
# Strip it so it is not repeated next to the formatted date in the message.
_TRAILING_DATE_RE = re.compile(r"\s*[-–—]?\s*\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4}\s*$")


def _title(value: object) -> str | None:
    text = _clean(value)
    if text is None:
        return None
    return _TRAILING_DATE_RE.sub("", text).strip() or text


def _venue(event: dict) -> str | None:
    arena = event.get("arena")
    if isinstance(arena, dict):
        return _clean(arena.get("name"))
    return _clean(arena)


def parse_next_data(html: str) -> list[Event]:
    match = NEXT_DATA_RE.search(html)
    if not match:
        return []
    try:
        groups = json.loads(match.group(1))["props"]["pageProps"]["events"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []

    seen_slugs: set[str] = set()
    events: list[Event] = []
    for group in groups:
        for event in group.get("events", []):
            slug = _clean(event.get("slug"))
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            events.append(
                Event(
                    id=slug,
                    url=f"{BASE_URL}/events/{slug}",
                    title=_title(event.get("title")),
                    date=dates.from_iso(event.get("start_date")),
                    venue=_venue(event),
                )
            )
    return events


def parse_links(html: str) -> list[Event]:
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


def parse_events(html: str) -> list[Event]:
    return parse_next_data(html) or parse_links(html)


class TicketXSource:
    key = "ticketx"
    display_name = "ticketx.com.mk"

    def fetch(self) -> list[Event]:
        with session() as s:
            response = s.get(PAGE_URL, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            html = response.text
        return parse_events(html)
