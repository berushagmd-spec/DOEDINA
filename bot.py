"""Telegram bot entry point for DERD GENERATOR 95.

No Telegram framework is needed: the bot talks to the official HTTP Bot API
using Python's standard library and receives updates through long polling.
"""

from __future__ import annotations

import html
import json
import logging
import os
import queue
import re
import signal
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from character_generators import (
    generate_nelis,
    generate_romix,
    generate_timur,
    nelis_combination_count,
    romix_combination_count,
    timur_combination_count,
)
from image_generator import random_hex, render_character, render_timur_with_derd
from name_generator import generate_name, raw_combination_count


APP_TITLE = "🟥DERD GENERATOR 95🟥"
CHARACTER_TITLES = {
    "derd": "🟥DERD GENERATOR 95🟥",
    "romix": "🟩ROMIX TATAR GENERATOR 95🟩",
    "nelis": "🟦DIMA NELIS GENERATOR 95🟦",
    "timur": "🟨TIMUR BABAEV GENERATOR 95🟨",
}
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


class GenerationCounter:
    """Thread-safe persistent generation counter."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._value = self._load()

    def _load(self) -> int:
        try:
            return max(0, int(self.path.read_text(encoding="utf-8").strip()))
        except (FileNotFoundError, ValueError, OSError):
            return 0

    def next(self) -> int:
        with self._lock:
            self._value += 1
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                temporary = self.path.with_name(f".{self.path.name}.tmp")
                temporary.write_text(str(self._value), encoding="utf-8")
                temporary.replace(self.path)
            except OSError as exc:
                logging.warning("Could not persist generation counter: %s", exc)
            return self._value


def parse_command(text: str, bot_username: str) -> str | None:
    """Parse a command with optional @ThisBot suffix, case-insensitively."""

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


def send_character(
    api: TelegramAPI,
    message: dict[str, Any],
    character: str,
    generation_counter: GenerationCounter | None = None,
    log_channel: str | None = None,
) -> None:
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

    if character == "derd":
        name = generate_name()
    elif character == "romix":
        name = " ".join(generate_romix())
    elif character == "nelis":
        name = " ".join(generate_nelis())
    elif character == "timur":
        name = " ".join(generate_timur())
    else:
        raise ValueError(f"Unknown character: {character}")

    color = random_hex()
    if character == "timur":
        photo = render_timur_with_derd(color).getvalue()
        filename = "timur.jpg"
        content_type = "image/jpeg"
    else:
        photo = render_character(character, color).getvalue()
        filename = f"{character}.png"
        content_type = "image/png"
    caption = (
        f"<b>{CHARACTER_TITLES[character]}</b>\n\n"
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
        files={"photo": (filename, photo, content_type)},
        timeout=45,
    )
    if generation_counter is not None and log_channel:
        generation_number = generation_counter.next()
        try:
            send_generation_log(
                api,
                log_channel,
                name,
                generation_number,
                filename,
                photo,
                content_type,
            )
        except TelegramAPIError as exc:
            logging.error(
                "Could not send generation #%s to %s: %s",
                generation_number,
                log_channel,
                exc,
            )

    logging.info(
        "Generated %s (%s) in %s for chat %s",
        name,
        character,
        color,
        chat_id,
    )


def send_generation_log(
    api: TelegramAPI,
    log_channel: str,
    name: str,
    generation_number: int,
    filename: str,
    photo: bytes,
    content_type: str,
) -> None:
    """Send one completed generation to the log channel with a strict caption."""

    fields = {
        "chat_id": log_channel,
        "caption": f"{html.escape(name)}\n#{generation_number} генерация",
        "parse_mode": "HTML",
    }
    last_error: TelegramAPIError | None = None
    for attempt in range(3):
        try:
            api.call(
                "sendPhoto",
                fields,
                files={"photo": (filename, photo, content_type)},
                timeout=45,
            )
            return
        except TelegramAPIError as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2**attempt)
    assert last_error is not None
    raise last_error


class GenerationQueue:
    """Single-worker FIFO queue that prevents concurrent image generation."""

    def __init__(
        self,
        api: TelegramAPI,
        generation_counter: GenerationCounter,
        log_channel: str,
        max_pending: int = 50,
    ):
        self.api = api
        self.generation_counter = generation_counter
        self.log_channel = log_channel
        self.max_pending = max_pending
        self._queue: queue.Queue[tuple[dict[str, Any], str] | None] = queue.Queue()
        self._lock = threading.Lock()
        self._pending = 0
        self._worker = threading.Thread(
            target=self._work,
            name="generation-worker",
            daemon=True,
        )
        self._worker.start()

    @property
    def pending(self) -> int:
        with self._lock:
            return self._pending

    def enqueue(self, message: dict[str, Any], character: str) -> bool:
        with self._lock:
            if self._pending >= self.max_pending:
                accepted = False
                position = 0
            else:
                self._pending += 1
                position = self._pending
                accepted = True

        if not accepted:
            send_text(
                self.api,
                message,
                "🚫 Очередь генераций заполнена. Попробуй чуть позже",
            )
            return False

        self._queue.put((message, character))
        if position > 1:
            try:
                send_text(
                    self.api,
                    message,
                    f"⏳ Добавлено в очередь. Позиция: {position}",
                )
            except TelegramAPIError:
                logging.debug("Could not send queue position", exc_info=True)
        return True

    def _work(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                self._queue.task_done()
                return
            message, character = item
            try:
                send_character(
                    self.api,
                    message,
                    character,
                    self.generation_counter,
                    self.log_channel,
                )
            except Exception:
                logging.exception("Queued %s generation failed", character)
                try:
                    send_text(
                        self.api,
                        message,
                        "❌ Генерация сломалась. Попробуй ещё раз",
                    )
                except Exception:
                    logging.debug("Could not report generation error", exc_info=True)
            finally:
                with self._lock:
                    self._pending -= 1
                self._queue.task_done()

    def shutdown(self) -> None:
        self._queue.put(None)
        self._worker.join(timeout=10)


WELCOME_TEXT = (
    "<b>ЖОСТКИЙ ЧЕЧЕНСКИЙ ГЕНЕРАТОР ГМД</b>\n\n"
    "/genderd - сгенерировать Дерда\n"
    "/genrom - сгенерировать Ромикса Татара\n"
    "/gennel - сгенерировать Диму Нелиса\n"
    "/gentim - сгенерировать Тимура Бабаева\n\n"
    "Команды работают и в личке, и в группах"
)


def handle_message(
    api: TelegramAPI,
    message: dict[str, Any],
    bot_username: str,
    generation_queue: GenerationQueue | None = None,
) -> None:
    text = message.get("text")
    if not isinstance(text, str):
        return
    command = parse_command(text, bot_username)
    character = {
        "genderd": "derd",
        "genrom": "romix",
        "gennel": "nelis",
        "gentim": "timur",
    }.get(command)
    if character is not None:
        if generation_queue is None:
            send_character(api, message, character)
        else:
            generation_queue.enqueue(message, character)
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
                        "command": "genderd",
                        "description": "Сгенерировать случайного Дерда",
                    },
                    {
                        "command": "genrom",
                        "description": "Сгенерировать Ромикса Татара",
                    },
                    {
                        "command": "gennel",
                        "description": "Сгенерировать Диму Нелиса",
                    },
                    {
                        "command": "gentim",
                        "description": "Сгенерировать Тимура Бабаева",
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
                    "Четыре огромных рофл-генератора: Дерд, Ромикс Татар, "
                    "Дима Нелис и Тимур Бабаев"
                )
            },
        ),
        (
            "setMyShortDescription",
            {"short_description": "Четыре персонажа и случайные имена"},
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

    counter_path = Path(
        os.environ.get(
            "GENERATION_COUNTER_FILE",
            str(ROOT / "generation_counter.txt"),
        )
    )
    generation_counter = GenerationCounter(counter_path)
    log_channel = os.environ.get("LOG_CHANNEL", "@GMDGenerator").strip()
    try:
        max_pending = max(1, int(os.environ.get("MAX_GENERATION_QUEUE", "50")))
    except ValueError:
        logging.warning("Invalid MAX_GENERATION_QUEUE; using 50")
        max_pending = 50
    generation_queue = GenerationQueue(
        api,
        generation_counter,
        log_channel,
        max_pending=max_pending,
    )
    logging.info("Generation log channel: %s", log_channel)
    logging.info("Generation counter file: %s", counter_path)

    logging.info("%s started as @%s", APP_TITLE, bot_username)
    logging.info(
        "Derd name space: %s",
        f"{raw_combination_count():,}".replace(",", " "),
    )
    logging.info(
        "Romix combinations: %s",
        f"{romix_combination_count():,}".replace(",", " "),
    )
    logging.info(
        "Nelis combinations: %s",
        f"{nelis_combination_count():,}".replace(",", " "),
    )
    logging.info(
        "Babaev combinations: %s",
        f"{timur_combination_count():,}".replace(",", " "),
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
                    handle_message(api, message, bot_username, generation_queue)
                except Exception:
                    logging.exception("Failed to handle update %s", update["update_id"])
        except TelegramAPIError as exc:
            if RUNNING:
                logging.warning("Polling error: %s; retry in %.0f sec", exc, retry_delay)
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30.0)

    generation_queue.shutdown()


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
