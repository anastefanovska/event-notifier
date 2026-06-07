from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol


@dataclass(frozen=True)
class Event:
    id: str
    url: str
    title: str | None = None
    date: str | None = None
    venue: str | None = None


class Source(Protocol):
    key: str
    display_name: str

    def fetch(self) -> Iterable[Event]: ...
