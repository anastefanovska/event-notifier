from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

DEFAULT_PATH = Path("state.json")
LEGACY_AVALON_FILE = Path("seen.txt")
LEGACY_AVALON_KEY = "avalon"


class State:
    def __init__(self, path: Path = DEFAULT_PATH) -> None:
        self._path = path
        self._data: dict[str, list[str]] = self._load()

    def _load(self) -> dict[str, list[str]]:
        if self._path.exists():
            with self._path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            return {k: list(v) for k, v in raw.items()}

        if LEGACY_AVALON_FILE.exists():
            ids = [line.strip() for line in LEGACY_AVALON_FILE.read_text().splitlines() if line.strip()]
            return {LEGACY_AVALON_KEY: ids}

        return {}

    def is_initialised(self, source_key: str) -> bool:
        return source_key in self._data

    def seen(self, source_key: str) -> set[str]:
        return set(self._data.get(source_key, []))

    def replace(self, source_key: str, ids: Iterable[str]) -> None:
        self._data[source_key] = sorted(set(ids))

    def save(self) -> None:
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, self._path)
