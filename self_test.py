"""Offline checks. Run with: python self_test.py"""

from __future__ import annotations

import io
import random
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image

from bot import (
    WELCOME_TEXT,
    GenerationCounter,
    GenerationQueue,
    configure_bot,
    parse_command,
    send_character,
    send_generation_log,
)
from character_generators import (
    BABAEV_CURATED,
    ETHNONYMS,
    SLAVIC_GIVEN_NAMES,
    WORLD_GIVEN_NAMES,
    generate_nelis,
    generate_romix,
    generate_timur,
    nelis_combination_count,
    romix_combination_count,
    timur_combination_count,
)
from image_generator import render_character, render_timur_with_derd
from name_generator import generate_name, raw_combination_count


class NameGeneratorTests(unittest.TestCase):
    def test_large_space(self):
        self.assertGreater(raw_combination_count(), 100_000_000_000)

    def test_names_are_valid(self):
        rng = random.Random(95)
        names = {generate_name(rng) for _ in range(10_000)}
        self.assertGreater(len(names), 5_000)
        for name in names:
            self.assertRegex(name, r"^[А-ЯЁ][а-яё]{2,12}$")
            self.assertTrue(name.casefold().endswith(("ерд", "рд", "ед")))


class CharacterGeneratorTests(unittest.TestCase):
    def test_large_spaces(self):
        self.assertGreater(romix_combination_count(), 1_000_000_000)
        self.assertGreater(nelis_combination_count(), 1_000_000_000)
        self.assertGreater(timur_combination_count(), 1_000_000_000)

    def test_romix_rules(self):
        rng = random.Random(951)
        generated = [generate_romix(rng) for _ in range(10_000)]
        self.assertGreater(len(set(generated)), 8_000)
        known_ethnonyms = {value.capitalize() for value in ETHNONYMS}
        for name, ethnonym in generated:
            self.assertTrue(name.casefold().endswith("икс"))
            self.assertIn(ethnonym, known_ethnonyms)

    def test_nelis_rules(self):
        rng = random.Random(952)
        generated = [generate_nelis(rng) for _ in range(10_000)]
        self.assertGreater(len(set(generated)), 7_000)
        known_names = set(SLAVIC_GIVEN_NAMES) | set(WORLD_GIVEN_NAMES)
        for given_name, surname in generated:
            self.assertIn(given_name, known_names)
            self.assertTrue(surname.casefold().endswith("ис"))

    def test_timur_rules(self):
        rng = random.Random(953)
        generated = [generate_timur(rng) for _ in range(10_000)]
        self.assertGreater(len(set(generated)), 7_000)
        known_names = set(SLAVIC_GIVEN_NAMES) | set(WORLD_GIVEN_NAMES)
        self.assertTrue(all(value.casefold().endswith("ев") for value in BABAEV_CURATED))
        self.assertIn("Тимур", {given_name for given_name, _surname in generated})
        for given_name, surname in generated:
            self.assertIn(given_name, known_names)
            self.assertTrue(surname.casefold().endswith("ев"))


class ImageGeneratorTests(unittest.TestCase):
    def _render(self, character):
        output = render_character(character, "#12ABEF")
        self.assertTrue(output.getvalue().startswith(b"\x89PNG\r\n\x1a\n"))
        return Image.open(io.BytesIO(output.getvalue())).convert("RGB")

    def test_derd_recolor(self):
        image = self._render("derd")
        self.assertEqual(image.size, (1536, 1523))
        self.assertEqual(image.getpixel((768, 100)), (0x12, 0xAB, 0xEF))
        self.assertEqual(image.getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(image.getpixel((500, 450)), (255, 255, 255))

    def test_romix_recolor(self):
        image = self._render("romix")
        self.assertEqual(image.size, (1536, 1536))
        self.assertEqual(image.getpixel((768, 768)), (0x12, 0xAB, 0xEF))
        self.assertEqual(image.getpixel((768, 100)), (0, 0, 0))
        self.assertEqual(image.getpixel((100, 100)), (255, 255, 255))

    def test_nelis_recolor(self):
        image = self._render("nelis")
        self.assertEqual(image.size, (1536, 1536))
        recolored = image.getpixel((200, 200))
        for actual, expected in zip(recolored, (0x12, 0xAB, 0xEF)):
            self.assertLessEqual(abs(actual - expected), 1)
        self.assertEqual(image.getpixel((768, 100)), (0, 0, 0))
        self.assertNotEqual(image.getpixel((768, 1350)), (128, 128, 128))
        self.assertEqual(image.getpixel((768, 1450)), (0, 0, 0))

    def test_timur_photo(self):
        path = Path(__file__).with_name("timur_template.jpg")
        with Image.open(path) as image:
            self.assertEqual(image.size, (1536, 1536))
            self.assertEqual(image.format, "JPEG")

        generated = render_timur_with_derd("#12ABEF", random.Random(95))
        self.assertTrue(generated.getvalue().startswith(b"\xff\xd8\xff"))
        self.assertNotEqual(generated.getvalue(), path.read_bytes())
        with Image.open(io.BytesIO(generated.getvalue())) as image:
            self.assertEqual(image.size, (1536, 1536))


class CommandTests(unittest.TestCase):
    def test_generator_commands(self):
        self.assertEqual(parse_command("/genderd", "DerdBot"), "genderd")
        self.assertEqual(parse_command("/GENROM", "DerdBot"), "genrom")
        self.assertEqual(
            parse_command("/GeNnEl@DerdBot", "DerdBot"), "gennel"
        )
        self.assertEqual(parse_command("/GENTIM", "DerdBot"), "gentim")

    def test_ignores_another_bot(self):
        self.assertIsNone(parse_command("/generate@OtherBot", "DerdBot"))
        self.assertIsNone(parse_command("просто текст", "DerdBot"))

    def test_help_and_menu_use_only_new_commands(self):
        self.assertNotIn("/generate\n", WELCOME_TEXT)
        self.assertNotIn("Теперь здесь три генератора", WELCOME_TEXT)
        self.assertIn("ЖОСТКИЙ ЧЕЧЕНСКИЙ ГЕНЕРАТОР ГМД", WELCOME_TEXT)
        for command in ("/genderd", "/genrom", "/gennel", "/gentim"):
            self.assertIn(command, WELCOME_TEXT)

        class FakeAPI:
            def __init__(self):
                self.calls = []

            def call(self, method, data):
                self.calls.append((method, data))
                return True

        api = FakeAPI()
        configure_bot(api)
        commands = api.calls[0][1]["commands"]
        command_names = [item["command"] for item in commands]
        self.assertEqual(
            command_names,
            ["genderd", "genrom", "gennel", "gentim", "help"],
        )

    def test_timur_sends_jpeg_with_hex_derd(self):
        class FakeAPI:
            def __init__(self):
                self.calls = []

            def call(self, method, data=None, files=None, timeout=30):
                self.calls.append((method, data, files, timeout))
                return True

        api = FakeAPI()
        message = {"chat": {"id": 95}, "message_id": 1}
        with TemporaryDirectory() as directory:
            counter = GenerationCounter(Path(directory) / "counter.txt")
            send_character(
                api,
                message,
                "timur",
                counter,
                "@GMDGenerator",
            )
        photo_calls = [call for call in api.calls if call[0] == "sendPhoto"]
        self.assertEqual(len(photo_calls), 2)
        user_photo, log_photo = photo_calls
        self.assertIn("HEX:", user_photo[1]["caption"])
        filename, content, content_type = user_photo[2]["photo"]
        self.assertEqual(filename, "timur.jpg")
        self.assertEqual(content_type, "image/jpeg")
        self.assertTrue(content.startswith(b"\xff\xd8\xff"))
        self.assertNotEqual(
            content,
            Path(__file__).with_name("timur_template.jpg").read_bytes(),
        )
        self.assertEqual(log_photo[1]["chat_id"], "@GMDGenerator")
        self.assertTrue(log_photo[1]["caption"].endswith("\n#1 генерация"))


class QueueAndLogTests(unittest.TestCase):
    class FakeAPI:
        def __init__(self):
            self.calls = []
            self.lock = threading.Lock()

        def call(self, method, data=None, files=None, timeout=30):
            with self.lock:
                self.calls.append((method, data, files, timeout))
            return True

    def test_counter_survives_restart(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "counter.txt"
            counter = GenerationCounter(path)
            self.assertEqual(counter.next(), 1)
            self.assertEqual(counter.next(), 2)
            restarted = GenerationCounter(path)
            self.assertEqual(restarted.next(), 3)

    def test_log_caption_has_exact_two_line_format(self):
        api = self.FakeAPI()
        send_generation_log(
            api,
            "@GMDGenerator",
            "Тимур Бабаев",
            95,
            "timur.jpg",
            b"jpeg",
            "image/jpeg",
        )
        method, data, files, _timeout = api.calls[0]
        self.assertEqual(method, "sendPhoto")
        self.assertEqual(data["chat_id"], "@GMDGenerator")
        self.assertEqual(data["caption"], "Тимур Бабаев\n#95 генерация")
        self.assertEqual(files["photo"][0], "timur.jpg")

    def test_second_generation_waits_in_fifo_queue(self):
        api = self.FakeAPI()
        first_started = threading.Event()
        release_first = threading.Event()
        state_lock = threading.Lock()
        order = []
        active = 0
        maximum_active = 0

        def fake_send_character(
            _api,
            _message,
            character,
            _counter,
            _log_channel,
        ):
            nonlocal active, maximum_active
            with state_lock:
                active += 1
                maximum_active = max(maximum_active, active)
                order.append(character)
            if character == "derd":
                first_started.set()
                release_first.wait(timeout=3)
            with state_lock:
                active -= 1

        with TemporaryDirectory() as directory:
            counter = GenerationCounter(Path(directory) / "counter.txt")
            with patch("bot.send_character", side_effect=fake_send_character):
                generation_queue = GenerationQueue(
                    api,
                    counter,
                    "@GMDGenerator",
                )
                first_message = {"chat": {"id": 1}, "message_id": 1}
                second_message = {"chat": {"id": 2}, "message_id": 2}
                self.assertTrue(generation_queue.enqueue(first_message, "derd"))
                self.assertTrue(first_started.wait(timeout=2))
                self.assertTrue(generation_queue.enqueue(second_message, "romix"))
                release_first.set()

                deadline = time.monotonic() + 3
                while generation_queue.pending and time.monotonic() < deadline:
                    time.sleep(0.01)
                generation_queue.shutdown()

        self.assertEqual(order, ["derd", "romix"])
        self.assertEqual(maximum_active, 1)
        notices = [
            data["text"]
            for method, data, _files, _timeout in api.calls
            if method == "sendMessage"
        ]
        self.assertIn("⏳ Добавлено в очередь. Позиция: 2", notices)


if __name__ == "__main__":
    unittest.main(verbosity=2)
