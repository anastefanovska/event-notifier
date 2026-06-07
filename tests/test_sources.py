"""Parser tests for each source, run against captured fixtures.

The scrapers/JSON-extractors are the most fragile part of the project — they
break whenever a site changes its markup. These tests exercise the pure parsing
functions offline so regressions are caught without hitting the network.
"""
from __future__ import annotations

import json
from pathlib import Path

from notifier.sources import _etickets_asmx, karti, mktickets, ticketx, wayin

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_etickets_asmx_parses_and_dedupes():
    payload = json.loads(_read("etickets_grouped.json"))
    events = _etickets_asmx.parse_grouped_events(
        payload, "https://example.mk/event?id={id}", "https://example.mk"
    )

    assert [e.id for e in events] == ["12345", "67890"]  # duplicate dropped

    first = events[0]
    assert first.url == "https://example.mk/event?id=12345"
    assert first.title == "Concert A"
    assert first.date == "19.06.2026"  # from the .NET /Date(...)/ epoch
    assert first.venue == "Arena Skopje"
    assert first.image == "https://example.mk/images/event/concert_a.jpg"

    assert events[1].image is None  # no Image field -> None

    second = events[1]
    assert second.date == "28.11.2026"  # from the numeric Date field
    assert second.venue == "Hall 2"  # falls back to Object when ObjectMap absent


def test_karti_parses_cards_and_dedupes():
    events = karti.parse_events(_read("karti.html"))

    assert [e.id for e in events] == ["steve-aoki.nspx", "monthly-repertoire.nspx"]

    aoki = events[0]
    assert aoki.url == "https://www.karti.com.mk/steve-aoki.nspx"
    assert aoki.title == "Steve Aoki"
    assert aoki.date == "05–12.06.2026"  # day range, mixed-language month
    assert aoki.venue == "Boris Trajkovski"
    assert aoki.image == "https://www.karti.com.mk/content/steve-aoki.jpg?ver001"

    # Unrecognised "month" text yields no date rather than garbage.
    assert events[1].date is None


def test_mktickets_parses_spans():
    events = mktickets.parse_events(_read("mktickets.html"))

    assert [e.id for e in events] == ["some-show", "another-night"]

    show = events[0]
    assert show.url == "https://mktickets.mk/event/some-show/"
    assert show.title == "Some Show"
    assert show.date == "26.06.2026"
    assert show.venue == "Skopje"
    assert show.image == "https://mktickets.mk/wp-content/uploads/some-show.png"


def test_ticketx_parses_next_data():
    events = ticketx.parse_events(_read("ticketx.html"))

    assert [e.id for e in events] == ["event-one", "event-two"]

    one = events[0]
    assert one.url == "https://ticketx.com.mk/events/event-one"
    assert one.title == "Event One - SKOPJE"  # trailing date stripped
    assert one.date == "15.05.2026"
    assert one.venue == "Arena X"
    assert one.image == "https://api.ticketx.com.mk/images/event-one.jpg"

    # arena can be a bare string instead of an object.
    assert events[1].venue == "Open Air Theatre"


def test_ticketx_falls_back_to_links():
    events = ticketx.parse_events(_read("ticketx_links.html"))
    assert [e.id for e in events] == ["legacy-one", "legacy-two"]
    assert events[0].url == "https://ticketx.com.mk/events/legacy-one"


def test_wayin_parses_next_data():
    events = wayin.parse_events(_read("wayin.html"))

    assert [e.id for e in events] == ["show-x", "show-y"]

    x = events[0]
    assert x.url == "https://wayin.mk/shop/events/show-x"
    assert x.title == "Show X"
    assert x.date == "20.07.2026"
    assert x.venue == "Ohrid"
    assert x.image == "https://content.wayin.mk/abc/images/show-x.jpg"

    assert events[1].date == "01.09.2026"  # DD-MM-YYYY normalised
