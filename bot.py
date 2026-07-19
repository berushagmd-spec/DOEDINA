"""Telegram bot entry point for DERD GENERATOR 95.

No Telegram framework is needed: the bot talks to the official HTTP Bot API
using Python's standard library and receives updates through long polling.
"""

from __future__ import annotations

import html
import json
import logging
import os
import re
import signal
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from image_generator import random_hex, render_cube
from name_generator import generate_name, raw_combination_count


APP_TITLE = "🟥DERD GENERATOR 95🟥"
ROOT = Path(__file__).resolve().parent
COMMAND_RE = re.compile(r"^/([A-Za-z0-9_]+)(?:@([A-Za-z0-9_]+))?(?:\s|$)")
RUNNING = True


class TelegramAPIError(RuntimeError):
    pass


def load_local_env(path: Path = ROOT / ".env") -> None:
    """Load simple KEY=VALUE lines without adding a dotenv dependency."""

    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _multipart_body(
    fields: dict[str, Any],
    files: dict[str, tuple[str, bytes, str]],
) -> tuple[bytes, str]:
    boundary = f"----DerdGenerator{uuid.uuid4().hex}"
    body = bytearray()

    def add(value: bytes) -> None:
        body.extend(value)
        body.extend(b"\r\n")

    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, (dict, list, bool)):
            value = json.dumps(value, ensure_ascii=False)
        add(f"--{boundary}".encode())
        add(f'Content-Disposition: form-data; name="{key}"'.encode())
        add(b"")
        add(str(value).encode("utf-8"))

    for key, (filename, content, content_type) in files.items():
        add(f"--{boundary}".encode())
        add(
            f'Content-Disposition: form-data; name="{key}"; '
            f'filename="{filename}"'.encode()
        )
        add(f"Content-Type: {content_type}".encode())
        add(b"")
        add(content)

    body.extend(f"--{boundary}--\r\n".encode())
    return bytes(body), f"multipart/form-data; boundary={boundary}"


class TelegramAPI:
    def __init__(self, token: str):
        self.base_url = f"https://api.telegram.org/bot{token}/"

    def call(
        self,
        method: str,
        data: dict[str, Any] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
        timeout: float = 30,
    ) -> Any:
        data = data or {}
        headers = {"User-Agent": "DerdGenerator95/1.0"}

        if files:
            body, content_type = _multipart_body(data, files)
            headers["Content-Type"] = content_type
        else:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"

        request = Request(
            self.base_url + method,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise TelegramAPIError(f"HTTP {exc.code}: {details}") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise TelegramAPIError(str(exc)) from exc

        if not payload.get("ok"):
            raise TelegramAPIError(payload.get("description", "Telegram API error"))
        return payload.get("result")


def parse_command(text: str, bot_username: str) -> str | None:
    """Parse /generate, /GENERATE and /generate@ThisBot safely."""

    match = COMMAND_RE.match(text.strip())
    if not match:
        return None
    command, mentioned_bot = match.groups()
    if mentioned_bot and mentioned_bot.casefold() != bot_username.casefold():
        return None
    return command.casefold()


def _thread_fields(message: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if message.get("message_thread_id") is not None:
        fields["message_thread_id"] = message["message_thread_id"]
    return fields


def send_text(api: TelegramAPI, message: dict[str, Any], text: str) -> None:
    fields = {
        "chat_id": message["chat"]["id"],
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        "reply_parameters": {
            "message_id": message["message_id"],
            "allow_sending_without_reply": True,
        },
        **_thread_fields(message),
    }
    api.call("sendMessage", fields)


def send_derd(api: TelegramAPI, message: dict[str, Any]) -> None:
    chat_id = message["chat"]["id"]
    action_fields = {
        "chat_id": chat_id,
        "action": "upload_photo",
        **_thread_fields(message),
    }
    try:
        api.call("sendChatAction", action_fields)
    except TelegramAPIError:
        logging.debug("Could not send chat action", exc_info=True)

    name = generate_name()
    color = random_hex()
    photo = render_cube(color).getvalue()
    caption = (
        f"<b>{APP_TITLE}</b>\n\n"
        f"<b>Имя:</b> {html.escape(name)}\n"
        f"<b>HEX:</b> <code>{color}</code>"
    )
    fields = {
        "chat_id": chat_id,
        "caption": caption,
        "parse_mode": "HTML",
        "reply_parameters": {
            "message_id": message["message_id"],
            "allow_sending_without_reply": True,
        },
        **_thread_fields(message),
    }
    api.call(
        "sendPhoto",
        fields,
        files={"photo": ("derd.png", photo, "image/png")},
        timeout=45,
    )
    logging.info("Generated %s in %s for chat %s", name, color, chat_id)


WELCOME_TEXT = (
    f"<b>{APP_TITLE}</b>\n\n"
    "Генерирую случайного Дерда: новое имя и новый цвет куба каждый раз\n\n"
    "Команда: /generate\n"
    "Она работает и в личке, и в группах. Вариант /GENERATE тоже принимается"
)


def handle_message(
    api: TelegramAPI,
    message: dict[str, Any],
    bot_username: str,
) -> None:
    text = message.get("text")
    if not isinstance(text, str):
        return
    command = parse_command(text, bot_username)
    if command == "generate":
        send_derd(api, message)
    elif command in {"start", "help"}:
        send_text(api, message, WELCOME_TEXT)


def configure_bot(api: TelegramAPI) -> None:
    """Create the visible command hint and bot profile text on every start."""

    operations = (
        (
            "setMyCommands",
            {
                "commands": [
                    {
                        "command": "generate",
                        "description": "Сгенерировать случайного Дерда",
                    },
                    {"command": "help", "description": "Как пользоваться ботом"},
                ]
            },
        ),
        ("setMyName", {"name": APP_TITLE}),
        (
            "setMyDescription",
            {
                "description": (
                    "Огромный генератор Дердов. Случайное имя и случайный HEX-цвет "
                    "куба по команде /generate"
                )
            },
        ),
        (
            "setMyShortDescription",
            {"short_description": "Случайные Дерды, имена и HEX-цвета"},
        ),
    )
    for method, data in operations:
        try:
            api.call(method, data)
        except TelegramAPIError as exc:
            logging.warning("Profile setup %s failed: %s", method, exc)


def _stop(_signum, _frame) -> None:
    global RUNNING
    RUNNING = False


def run() -> None:
    load_local_env()
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "BOT_TOKEN не найден. Скопируй .env.example в .env и вставь токен."
        )

    api = TelegramAPI(token)
    me = api.call("getMe")
    bot_username = me["username"]

    # Long polling and webhooks cannot run together.
    api.call("deleteWebhook", {"drop_pending_updates": False})
    configure_bot(api)

    logging.info("%s started as @%s", APP_TITLE, bot_username)
    logging.info(
        "Raw procedural name space: %s",
        f"{raw_combination_count():,}".replace(",", " "),
    )

    offset: int | None = None
    retry_delay = 1.0
    while RUNNING:
        fields: dict[str, Any] = {
            "timeout": 45,
            "limit": 100,
            "allowed_updates": ["message"],
        }
        if offset is not None:
            fields["offset"] = offset

        try:
            updates = api.call("getUpdates", fields, timeout=55)
            retry_delay = 1.0
            for update in updates:
                offset = update["update_id"] + 1
                message = update.get("message")
                if not isinstance(message, dict):
                    continue
                try:
                    handle_message(api, message, bot_username)
                except Exception:
                    logging.exception("Failed to handle update %s", update["update_id"])
        except TelegramAPIError as exc:
            if RUNNING:
                logging.warning("Polling error: %s; retry in %.0f sec", exc, retry_delay)
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30.0)


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    try:
        run()
    except TelegramAPIError as exc:
        logging.critical("Telegram API: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
