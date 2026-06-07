from __future__ import annotations

import logging
import os

from requests.utils import requote_uri

from .http import DEFAULT_TIMEOUT, session

log = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"

# Telegram caps photo captions at 1024 chars; ours are far shorter, but guard
# against a pathologically long title pushing us over the limit.
MAX_CAPTION = 1024


class TelegramError(RuntimeError):
    """Raised when the Telegram Bot API rejects a request."""


class Telegram:
    def __init__(self, token: str | None = None, chat_id: str | None = None) -> None:
        self._token = token or os.environ["BOT_TOKEN"]
        self._chat_id = chat_id or os.environ["CHAT_ID"]
        self._session = session()

    def _post(self, method: str, payload: dict):
        return self._session.post(
            f"{API_BASE}/bot{self._token}/{method}",
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )

    def send(self, text: str, image: str | None = None) -> None:
        """Send a notification, as a photo with caption when an image is given.

        Falls back to a plain text message if the photo can't be sent (e.g. the
        source's image URL is unreachable), so the user is still notified.
        """
        if image:
            response = self._post(
                "sendPhoto",
                {
                    "chat_id": self._chat_id,
                    # Percent-encode so URLs with non-ASCII paths (e.g. Cyrillic
                    # filenames) are valid for Telegram's image fetcher.
                    "photo": requote_uri(image),
                    "caption": text[:MAX_CAPTION],
                    "parse_mode": "HTML",
                },
            )
            if response.ok:
                return
            log.warning(
                "sendPhoto failed (%s: %s); falling back to text",
                response.status_code,
                response.text,
            )

        response = self._post(
            "sendMessage",
            {
                "chat_id": self._chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
        )
        if not response.ok:
            # Telegram returns a JSON body describing exactly what went wrong;
            # surface it instead of a bare status code.
            raise TelegramError(
                f"Telegram API returned {response.status_code}: {response.text}"
            )
