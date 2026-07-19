"""Offline checks. Run with: python self_test.py"""

from __future__ import annotations

import io
import random
import unittest

from PIL import Image

from bot import parse_command
from image_generator import render_cube
from name_generator import generate_name, raw_combination_count


class NameGeneratorTests(unittest.TestCase):
    def test_large_space(self):
        self.assertGreater(raw_combination_count(), 1_000_000_000)

    def test_names_are_valid(self):
        rng = random.Random(95)
        names = {generate_name(rng) for _ in range(10_000)}
        self.assertGreater(len(names), 5_000)
        for name in names:
            self.assertRegex(name, r"^[А-ЯЁ][а-яё]{2,12}$")


class ImageGeneratorTests(unittest.TestCase):
    def test_recolor_preserves_face(self):
        output = render_cube("#12ABEF")
        self.assertTrue(output.getvalue().startswith(b"\x89PNG\r\n\x1a\n"))
        image = Image.open(io.BytesIO(output.getvalue())).convert("RGB")
        self.assertEqual(image.size, (1536, 1523))
        self.assertEqual(image.getpixel((768, 100)), (0x12, 0xAB, 0xEF))
        self.assertEqual(image.getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(image.getpixel((500, 450)), (255, 255, 255))


class CommandTests(unittest.TestCase):
    def test_generate_variants(self):
        self.assertEqual(parse_command("/generate", "DerdBot"), "generate")
        self.assertEqual(parse_command("/GENERATE", "DerdBot"), "generate")
        self.assertEqual(
            parse_command("/GeNeRaTe@DerdBot", "DerdBot"), "generate"
        )

    def test_ignores_another_bot(self):
        self.assertIsNone(parse_command("/generate@OtherBot", "DerdBot"))
        self.assertIsNone(parse_command("просто текст", "DerdBot"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
