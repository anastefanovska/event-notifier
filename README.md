# Event-notifier

Watches several Macedonian ticketing sites and sends a Telegram message when a
new event appears. It runs on a schedule in GitHub Actions, so you don't have to
keep refreshing the sites yourself.

## Sources

| Key         | Site             | How it's read                          |
|-------------|------------------|----------------------------------------|
| `avalon`    | avalonbooking.mk | eTickets ASMX JSON API                  |
| `kupikarta` | kupikarta.com    | eTickets ASMX JSON API                  |
| `karti`     | karti.com.mk     | HTML scrape of the home page            |
| `mktickets` | mktickets.mk     | HTML scrape of the home page            |
| `ticketx`   | ticketx.com.mk   | Next.js `__NEXT_DATA__` JSON (+ fallback) |
| `wayin`     | wayin.mk         | Next.js `__NEXT_DATA__` JSON (+ fallback) |

## How it works

1. Each source is fetched concurrently and normalised into `Event` objects
   (`notifier/source.py`). Dates from every site are converted to a single
   `DD.MM.YYYY` Europe/Skopje format by `notifier/dates.py`.
2. Seen event IDs are tracked per source in `state.json` (`notifier/state.py`).
3. On a source's **first run**, current events are recorded silently. After
   that, only IDs not already in `state.json` trigger a Telegram message.

## Configuration

Two environment variables are required:

| Variable    | Description                                              |
|-------------|----------------------------------------------------------|
| `BOT_TOKEN` | Telegram bot token from [@BotFather](https://t.me/BotFather). |
| `CHAT_ID`   | Chat/channel ID the bot posts to.                         |

In GitHub Actions these are read from repository **Secrets** of the same name.

## Run locally

```bash
python -m venv .venv
. .venv/Scripts/activate      # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

export BOT_TOKEN=...   # $env:BOT_TOKEN = "..." in PowerShell
export CHAT_ID=...
python -m notifier
```

The process exits non-zero if any source fails, so failures surface in CI.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

`tests/test_dates.py` covers date normalisation; `tests/test_sources.py` runs
each parser against captured fixtures in `tests/fixtures/` (no network).

## State in CI

`state.json` is persisted between scheduled runs with `actions/cache` rather
than committed back to the repository, so the commit history stays clean. The
copy checked into the repo is just the initial seed.
