"""Unit tests for the date-normalisation helpers.

These are pure (no network) and lock in the trickiest logic: parsing the messy,
mixed-language month names that karti.com.mk renders, plus the various date
shapes the other sources expose.
"""
from __future__ import annotations

from notifier import dates


def test_from_dotnet_epoch_to_skopje_local():
    # 1781895600000 ms == 2026-06-19 21:00 Europe/Skopje (summer, UTC+2)
    assert dates.from_dotnet("/Date(1781895600000)/") == "19.06.2026"


def test_from_dotnet_handles_garbage():
    assert dates.from_dotnet(None) is None
    assert dates.from_dotnet("not a date") is None


def test_from_iso_converts_to_local():
    assert dates.from_iso("2026-06-19T20:00:17.000000Z") == "19.06.2026"


def test_from_iso_handles_garbage():
    assert dates.from_iso("") is None
    assert dates.from_iso("nonsense") is None


def test_from_numeric_normalises_separators():
    assert dates.from_numeric("28.11.2026") == "28.11.2026"
    assert dates.from_numeric("26-06-2026") == "26.06.2026"
    assert dates.from_numeric("1/2/2026") == "01.02.2026"
    assert dates.from_numeric("Some text 05-08-2026 trailing") == "05.08.2026"
    assert dates.from_numeric(None) is None
    assert dates.from_numeric("no digits") is None


def test_from_named_macedonian_cyrillic():
    assert dates.from_named("12 Јуни 2026") == "12.06.2026"
    assert dates.from_named("10 Септември 2026") == "10.09.2026"


def test_from_named_day_range():
    assert dates.from_named("5-12 Јуни 2026") == "05–12.06.2026"


def test_from_named_latin_and_english_variants():
    # karti renders these inconsistently: Latin "Maj", English "October",
    # and mojibake "Aвгуст" (Latin "A" + Cyrillic).
    assert dates.from_named("28 Maj 2026") == "28.05.2026"
    assert dates.from_named("28 October 2026") == "28.10.2026"
    assert dates.from_named("15 Aвгуст 2026") == "15.08.2026"


def test_from_named_unknown_month_returns_none():
    # Unrecognised month -> None so callers can fall back rather than show junk.
    assert dates.from_named("15 Smonth 2026") is None
    assert dates.from_named("Месечен репертоар") is None
    assert dates.from_named(None) is None
