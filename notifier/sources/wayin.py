from __future__ import annotations

import json
import re

from .. import dates
from ..source import Event
from ..http import DEFAULT_TIMEOUT, session

PAGE_URL = "https://wayin.mk/shop/events"
BASE_URL = "https://wayin.mk"

# wayin.mk is a Next.js app; the events list is rendered server-side and the full
# structured data is embedded as JSON in the __NEXT_DATA__ script tag.
NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
# Fallback for older markup: plain anchors to event pages.
EVENT_LINK_RE = re.compile(r'href="(/shop/events/[a-z0-9-]+)"', re.IGNORECASE)


def _clean(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _image(product: dict) -> str | None:
    thumbnail = product.get("thumbnail")
    if isinstance(thumbnail, dict):
        return _clean(thumbnail.get("url"))
    return None


def parse_next_data(html: str) -> list[Event]:
    match = NEXT_DATA_RE.search(html)
    if not match:
        return []
    try:
        products = json.loads(match.group(1))["props"]["pageProps"]["products"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []

    seen_slugs: set[str] = set()
    events: list[Event] = []
    for product in products:
        slug = _clean(product.get("slug"))
        if not slug or slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        events.append(
            Event(
                id=slug,
                url=f"{BASE_URL}/shop/events/{slug}",
                title=_clean(product.get("title")),
                date=dates.from_numeric(product.get("event_date_period")),
                venue=_clean(product.get("event_location")),
                image=_image(product),
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


class WayInSource:
    key = "wayin"
    display_name = "wayin.mk"

    def fetch(self) -> list[Event]:
        with session() as s:
            response = s.get(PAGE_URL, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            html = response.text
        return parse_events(html)
