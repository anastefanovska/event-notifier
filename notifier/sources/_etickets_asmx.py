from __future__ import annotations

from typing import Iterator

from ..http import DEFAULT_TIMEOUT, session
from ..source import Event

EVENT_TYPE_SUFFIX = "EventModel"


def _clean(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _venue(raw: dict) -> str | None:
    for container in (raw.get("ObjectMap"), raw.get("Object")):
        if isinstance(container, dict):
            name = _clean(container.get("NameFirst"))
            if name:
                return name
    return None


def _price(raw: dict) -> str | None:
    amount = raw.get("PriceCurrencySecond") or raw.get("PriceCurrencyFirst")
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return f"{value:.0f} ден"


def _walk_events(data: object) -> Iterator[dict]:
    if isinstance(data, dict):
        if str(data.get("__type", "")).endswith(EVENT_TYPE_SUFFIX):
            yield data
            return
        for value in data.values():
            yield from _walk_events(value)
    elif isinstance(data, list):
        for item in data:
            yield from _walk_events(item)


def fetch_grouped_events(api_url: str, event_url_template: str, page_size: int = 50) -> list[Event]:
    """Fetch events from an eTickets ASMX `GetGroupedEvents` endpoint.

    `event_url_template` must contain a `{id}` placeholder.
    """
    with session() as s:
        response = s.post(
            api_url,
            json={"filter": {"Page": 1, "Size": page_size, "MobileEnabled": True}},
            headers={"Content-Type": "application/json; charset=UTF-8"},
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()

    seen_ids: set[str] = set()
    events: list[Event] = []
    for raw in _walk_events(payload.get("d")):
        raw_id = raw.get("Id")
        if raw_id is None:
            continue
        event_id = str(raw_id)
        if event_id in seen_ids:
            continue
        seen_ids.add(event_id)
        events.append(
            Event(
                id=event_id,
                url=event_url_template.format(id=event_id),
                title=_clean(raw.get("NameFirst")),
                date=_clean(raw.get("Date")),
                venue=_venue(raw),
                price=_price(raw),
            )
        )
    return events
