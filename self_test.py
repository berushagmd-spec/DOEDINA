"""Offline checks. Run with: python self_test.py"""

from __future__ import annotations

import io
import random
import unittest

from PIL import Image

from bot import WELCOME_TEXT, configure_bot, parse_command
from character_generators import (
    ETHNONYMS,
    SLAVIC_GIVEN_NAMES,
    WORLD_GIVEN_NAMES,
    generate_nelis,
    generate_romix,
    nelis_combination_count,
    romix_combination_count,
)
from image_generator import render_character
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


class CommandTests(unittest.TestCase):
    def test_generator_commands(self):
        self.assertEqual(parse_command("/genderd", "DerdBot"), "genderd")
        self.assertEqual(parse_command("/GENROM", "DerdBot"), "genrom")
        self.assertEqual(
            parse_command("/GeNnEl@DerdBot", "DerdBot"), "gennel"
        )

    def test_ignores_another_bot(self):
        self.assertIsNone(parse_command("/generate@OtherBot", "DerdBot"))
        self.assertIsNone(parse_command("просто текст", "DerdBot"))

    def test_help_and_menu_use_only_new_commands(self):
        self.assertNotIn("/generate\n", WELCOME_TEXT)
        self.assertNotIn("Теперь здесь три генератора", WELCOME_TEXT)
        self.assertIn("ЖОСТКИЙ ЧЕЧЕНСКИЙ ГЕНЕРАТОР ГМД", WELCOME_TEXT)
        for command in ("/genderd", "/genrom", "/gennel"):
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
        self.assertEqual(command_names, ["genderd", "genrom", "gennel", "help"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
