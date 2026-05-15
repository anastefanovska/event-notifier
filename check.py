from notifier import run
from notifier.sources import ALL_SOURCES
from notifier.state import State
from notifier.telegram import Telegram


def main() -> None:
    run(ALL_SOURCES, State(), Telegram())


if __name__ == "__main__":
    main()
