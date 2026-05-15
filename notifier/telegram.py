from __future__ import annotations

import os

import requests

API_BASE = "https://api.telegram.org"


class Telegram:
    def __init__(self, token: str | None = None, chat_id: str | None = None) -> None:
        self._token = token or os.environ["BOT_TOKEN"]
        self._chat_id = chat_id or os.environ["CHAT_ID"]

    def send(self, text: str) -> None:
        requests.post(
            f"{API_BASE}/bot{self._token}/sendMessage",
            data={
                "chat_id": self._chat_id,
                "text": text,
                "disable_web_page_preview": "false",
            },
            timeout=20,
        ).raise_for_status()
