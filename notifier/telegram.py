from __future__ import annotations

import os

from .http import DEFAULT_TIMEOUT, session

API_BASE = "https://api.telegram.org"


class TelegramError(RuntimeError):
    """Raised when the Telegram Bot API rejects a request."""


class Telegram:
    def __init__(self, token: str | None = None, chat_id: str | None = None) -> None:
        self._token = token or os.environ["BOT_TOKEN"]
        self._chat_id = chat_id or os.environ["CHAT_ID"]
        self._session = session()

    def send(self, text: str) -> None:
        response = self._session.post(
            f"{API_BASE}/bot{self._token}/sendMessage",
            json={
                "chat_id": self._chat_id,
                "text": text,
                "disable_web_page_preview": False,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        if not response.ok:
            # Telegram returns a JSON body describing exactly what went wrong;
            # surface it instead of a bare status code.
            raise TelegramError(
                f"Telegram API returned {response.status_code}: {response.text}"
            )
