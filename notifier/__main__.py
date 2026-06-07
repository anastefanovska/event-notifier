from __future__ import annotations

import logging

from . import run
from .sources import ALL_SOURCES
from .state import State
from .telegram import Telegram


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    failures = run(ALL_SOURCES, State(), Telegram())
    if failures:
        logging.getLogger(__name__).error("%d source(s) failed this run", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
