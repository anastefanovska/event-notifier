from __future__ import annotations

import concurrent.futures
import html
import logging
from typing import Sequence

from .source import Event, Source
from .state import State
from .telegram import Telegram

log = logging.getLogger(__name__)

# Sources are independent network calls, so fetch them concurrently rather than
# paying the sum of every site's latency on each run.
MAX_WORKERS = 8

# Short Macedonian label shown in place of the (often very long) event URL.
# Rendered as an HTML link so the message stays compact and tidy.
LINK_LABEL = "Погледни настан"


def _format_message(source: Source, event: Event) -> str:
    # Telegram is sent with parse_mode=HTML, so escape any user-facing text that
    # could contain &, < or > and break the markup.
    if event.title:
        lines = [f"🎟️ {html.escape(event.title)}"]
    else:
        lines = [f"🎟️ Нов настан на {html.escape(source.display_name)}"]
    if event.date:
        lines.append(f"📅 {html.escape(event.date)}")
    if event.venue:
        lines.append(f"📍 {html.escape(event.venue)}")
    url = html.escape(event.url, quote=True)
    lines.append(f'🔗 <a href="{url}">{LINK_LABEL}</a>')
    return "\n".join(lines)


def _fetch(source: Source) -> list[Event]:
    return list(source.fetch())


def run(sources: Sequence[Source], state: State, telegram: Telegram) -> int:
    """Fetch every source, notify on new events, and persist state.

    Returns the number of sources that failed (fetch error or notification
    error) so the caller can signal a non-zero exit and surface the failure
    in CI instead of silently passing.
    """
    fetched: dict[str, list[Event]] = {}
    failures = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_to_source = {pool.submit(_fetch, source): source for source in sources}
        for future in concurrent.futures.as_completed(future_to_source):
            source = future_to_source[future]
            try:
                fetched[source.key] = future.result()
            except Exception:
                failures += 1
                log.exception("[%s] fetch failed", source.key)

    # Process in declared order for deterministic, readable logs.
    for source in sources:
        events = fetched.get(source.key)
        if events is None:
            # Fetch failed; leave this source's state untouched so we don't
            # forget what we've seen and re-notify everything next run.
            continue

        current_ids = [event.id for event in events]
        first_run = not state.is_initialised(source.key)
        seen = state.seen(source.key)
        new_events = [event for event in events if event.id not in seen]

        if first_run:
            log.info(
                "[%s] first run — recording %d events, no notifications",
                source.key,
                len(current_ids),
            )
        else:
            for event in new_events:
                log.info("[%s] new event: %s", source.key, event.url)
                try:
                    telegram.send(_format_message(source, event), image=event.image)
                except Exception:
                    failures += 1
                    log.exception(
                        "[%s] telegram send failed for %s", source.key, event.url
                    )

        state.replace(source.key, current_ids)

    state.save()
    return failures
