from __future__ import annotations

import traceback
from typing import Sequence

from .source import Event, Source
from .state import State
from .telegram import Telegram


def _format_message(source: Source, event: Event) -> str:
    return f"🎟️ New event on {source.display_name}\n{event.url}"


def run(sources: Sequence[Source], state: State, telegram: Telegram) -> None:
    for source in sources:
        try:
            events = list(source.fetch())
        except Exception:
            print(f"[{source.key}] fetch failed:")
            traceback.print_exc()
            continue

        current_ids = [e.id for e in events]
        first_run = not state.is_initialised(source.key)
        seen = state.seen(source.key)
        new_events = [e for e in events if e.id not in seen]

        if first_run:
            print(f"[{source.key}] first run — recording {len(current_ids)} events, no notifications")
        else:
            for event in new_events:
                print(f"[{source.key}] new event: {event.url}")
                try:
                    telegram.send(_format_message(source, event))
                except Exception:
                    print(f"[{source.key}] telegram send failed for {event.url}:")
                    traceback.print_exc()

        state.replace(source.key, current_ids)

    state.save()
