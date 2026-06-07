"""Date normalisation helpers.

Every source exposes dates in a different shape and language (.NET epoch,
ISO timestamps, numeric strings, messy Macedonian/English month names). These
helpers turn all of them into a single, language-neutral ``DD.MM.YYYY`` string
so notifications look identical regardless of the source.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo

    _TZ: timezone | "ZoneInfo" = ZoneInfo("Europe/Skopje")
except Exception:  # pragma: no cover - zoneinfo/tzdata unavailable
    _TZ = timezone(timedelta(hours=1))

_DOTNET_RE = re.compile(r"/Date\((-?\d+)")
_NUMERIC_RE = re.compile(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})")
_KARTI_RE = re.compile(r"(\d{1,2})(?:\s*-\s*(\d{1,2}))?\s+(\S+)\s+(\d{4})")

# Month keys cover Macedonian (Cyrillic), transliterated, and English spellings.
# Some are stems (e.g. "вгуст") so we still match mojibake like the Latin-"A"
# "Aвгуст" that karti.com.mk occasionally renders.
_MONTH_KEYS: dict[int, tuple[str, ...]] = {
    1: ("јануари", "januari", "january"),
    2: ("февруари", "februari", "february"),
    3: ("март", "mart", "march"),
    4: ("април", "april"),
    5: ("мај", "maj", "may"),
    6: ("јуни", "juni", "june"),
    7: ("јули", "juli", "july"),
    8: ("вгуст", "avgust", "august"),
    9: ("септември", "septemvri", "september"),
    10: ("октомври", "oktomvri", "october"),
    11: ("ноември", "noemvri", "november"),
    12: ("декември", "dekemvri", "december"),
}


def _fmt(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y")


def _month_number(name: str) -> int | None:
    text = name.strip().lower()
    for number, keys in _MONTH_KEYS.items():
        if any(text.startswith(key) or key in text for key in keys):
            return number
    return None


def from_epoch_ms(value: object) -> str | None:
    try:
        ms = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    try:
        return _fmt(datetime.fromtimestamp(ms / 1000, _TZ))
    except (OverflowError, OSError, ValueError):
        return None


def from_dotnet(value: object) -> str | None:
    """Parse an ASP.NET ``/Date(1781895600000)/`` string."""
    if value is None:
        return None
    match = _DOTNET_RE.search(str(value))
    return from_epoch_ms(match.group(1)) if match else None


def from_iso(value: object) -> str | None:
    """Parse an ISO-8601 timestamp, converting to Skopje local time."""
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(_TZ)
    return _fmt(dt)


def from_numeric(value: object) -> str | None:
    """Parse ``DD.MM.YYYY`` / ``DD-MM-YYYY`` / ``DD/MM/YYYY`` into ``DD.MM.YYYY``."""
    if not value:
        return None
    match = _NUMERIC_RE.search(str(value))
    if not match:
        return None
    day, month, year = match.groups()
    return f"{int(day):02d}.{int(month):02d}.{year}"


def from_named(value: object) -> str | None:
    """Parse ``"5-12 Јуни 2026"`` / ``"12 Septemvri 2026"`` into ``DD.MM.YYYY``.

    Day ranges are rendered as ``DD–DD.MM.YYYY``. Returns ``None`` if the month
    name is unrecognised so callers can fall back rather than show garbage.
    """
    if not value:
        return None
    match = _KARTI_RE.search(str(value))
    if not match:
        return None
    first_day, last_day, month_name, year = match.groups()
    month = _month_number(month_name)
    if month is None:
        return None
    if last_day:
        return f"{int(first_day):02d}–{int(last_day):02d}.{month:02d}.{year}"
    return f"{int(first_day):02d}.{month:02d}.{year}"
