from __future__ import annotations

from typing import Iterator

from ..http import DEFAULT_TIMEOUT, session
from ..source import Event

EVENT_TYPE_SUFFIX = "EventModel"


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
        events.append(Event(id=event_id, url=event_url_template.format(id=event_id)))
    return events
