"""Fast HEX recoloring for all three supplied character templates."""

from __future__ import annotations

import io
import random
import re
import secrets
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parent
TEMPLATE_SPECS = {
    "derd": ("cube_template.png", (254, 0, 0)),
    "romix": ("romix_template.png", (126, 255, 175)),
    "nelis": ("nelis_template.png", (18, 134, 255)),
}
_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_SYSTEM_RANDOM = random.SystemRandom()


def random_hex() -> str:
    """Return a uniformly random 24-bit RGB color."""

    return f"#{secrets.randbelow(0x1000000):06X}"


def _parse_hex(hex_color: str) -> tuple[int, int, int]:
    if _HEX_RE.fullmatch(hex_color) is None:
        raise ValueError("Color must look like #12ABEF")
    return tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))


@lru_cache(maxsize=len(TEMPLATE_SPECS))
def _template_parts(character: str):
    """Extract a neutral base and color mask from one character template.

    The math treats colored pixels as a mixture of the template's source color
    and a neutral gray. This keeps black/white details and soft gradients while
    mapping the main fill to the exact requested HEX value.
    """

    try:
        filename, source_color = TEMPLATE_SPECS[character]
    except KeyError as exc:
        raise ValueError(f"Unknown character: {character}") from exc

    with Image.open(ROOT / filename) as source:
        rgb = source.convert("RGB")

    red, green, blue = rgb.split()
    maximum = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    minimum = ImageChops.darker(ImageChops.darker(red, green), blue)
    chroma = ImageChops.subtract(maximum, minimum)

    source_minimum = min(source_color)
    source_chroma = max(source_color) - source_minimum
    mask = chroma.point(
        lambda value: (
            0
            if value < 6
            else min(255, round(value * 255 / source_chroma))
        )
    )

    colored_minimum = ImageChops.multiply(
        Image.new("L", mask.size, source_minimum),
        mask,
    )
    neutral_base = ImageChops.subtract(minimum, colored_minimum)
    return neutral_base, mask


def render_character(character: str, hex_color: str) -> io.BytesIO:
    """Recolor one character and return a ready-to-upload PNG."""

    target = _parse_hex(hex_color)
    neutral_base, mask = _template_parts(character)

    channels = tuple(
        ImageChops.add(
            neutral_base,
            ImageChops.multiply(Image.new("L", mask.size, component), mask),
        )
        for component in target
    )
    result = Image.merge("RGB", channels)

    output = io.BytesIO()
    output.name = f"{character}.png"
    result.save(output, format="PNG", optimize=True, compress_level=7)
    output.seek(0)
    return output


def render_cube(hex_color: str) -> io.BytesIO:
    """Backward-compatible wrapper for the original Derd generator."""

    return render_character("derd", hex_color)


def render_timur_with_derd(
    hex_color: str,
    rng: random.Random | random.SystemRandom | None = None,
) -> io.BytesIO:
    """Attach a randomly placed HEX-colored Derd sticker to Timur's face."""

    rng = rng or _SYSTEM_RANDOM
    with Image.open(ROOT / "timur_template.jpg") as source:
        base = source.convert("RGBA")

    with Image.open(render_character("derd", hex_color)) as source:
        # Remove the large outer black margin while keeping Derd's black face.
        sticker = source.convert("RGB").crop((65, 58, 1471, 1464))

    size = rng.randint(340, 470)
    sticker = sticker.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    rounded_mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(rounded_mask).rounded_rectangle(
        (0, 0, size - 1, size - 1),
        radius=max(18, size // 14),
        fill=255,
    )
    sticker.putalpha(rounded_mask)
    sticker = sticker.rotate(
        rng.uniform(-14, 14),
        resample=Image.Resampling.BICUBIC,
        expand=True,
    )

    centers = (
        (650, 430),
        (850, 500),
        (610, 700),
        (890, 720),
        (760, 600),
    )
    center_x, center_y = rng.choice(centers)
    left = center_x - sticker.width // 2
    top = center_y - sticker.height // 2
    base.alpha_composite(sticker, dest=(left, top))

    output = io.BytesIO()
    output.name = "timur.jpg"
    base.convert("RGB").save(output, format="JPEG", quality=92, optimize=True)
    output.seek(0)
    return output


if __name__ == "__main__":
    for character in TEMPLATE_SPECS:
        color = random_hex()
        preview = ROOT / f"preview_{character}.png"
        preview.write_bytes(render_character(character, color).getvalue())
        print(f"Создан {preview.name}: {color}")
    color = random_hex()
    preview = ROOT / "preview_timur.jpg"
    preview.write_bytes(render_timur_with_derd(color).getvalue())
    print(f"Создан {preview.name}: {color}")
