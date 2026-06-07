from __future__ import annotations

from typing import Iterator

from .. import dates
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


def parse_grouped_events(payload: object, event_url_template: str) -> list[Event]:
    """Turn an eTickets ASMX response payload into events.

    ``event_url_template`` must contain a ``{id}`` placeholder. Pure function
    (no network) so it can be exercised against captured fixtures.
    """
    root = payload.get("d") if isinstance(payload, dict) else payload

    seen_ids: set[str] = set()
    events: list[Event] = []
    for raw in _walk_events(root):
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
                date=dates.from_dotnet(raw.get("DateTime")) or dates.from_numeric(raw.get("Date")),
                venue=_venue(raw),
            )
        )
    return events


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

    return parse_grouped_events(payload, event_url_template)
