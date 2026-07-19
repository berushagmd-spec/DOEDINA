"""Fast recoloring of the supplied Geometry Dash cube template."""

from __future__ import annotations

import io
import re
import secrets
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops


TEMPLATE_PATH = Path(__file__).with_name("cube_template.png")
_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def random_hex() -> str:
    """Return a uniformly random 24-bit RGB color."""

    return f"#{secrets.randbelow(0x1000000):06X}"


def _parse_hex(hex_color: str) -> tuple[int, int, int]:
    if _HEX_RE.fullmatch(hex_color) is None:
        raise ValueError("Color must look like #12ABEF")
    return tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))


@lru_cache(maxsize=1)
def _template_parts():
    """Precompute the red contribution so black and white stay untouched."""

    with Image.open(TEMPLATE_PATH) as source:
        rgb = source.convert("RGB")

    red, green, blue = rgb.split()
    strongest_non_red = ImageChops.lighter(green, blue)
    red_mask = ImageChops.subtract(red, strongest_non_red)

    # JPEG compression left the large red field at 253-254 instead of 255.
    # Snap only those near-solid pixels to full strength; the soft glow keeps
    # its original intensity.
    red_mask = red_mask.point(lambda value: 255 if value >= 240 else value)

    base_red = ImageChops.subtract(red, red_mask)
    return base_red, green, blue, red_mask


def render_cube(hex_color: str) -> io.BytesIO:
    """Recolor only red-tinted pixels and return a ready-to-upload PNG."""

    target_red, target_green, target_blue = _parse_hex(hex_color)
    base_red, base_green, base_blue, mask = _template_parts()

    tint_red = ImageChops.multiply(Image.new("L", mask.size, target_red), mask)
    tint_green = ImageChops.multiply(Image.new("L", mask.size, target_green), mask)
    tint_blue = ImageChops.multiply(Image.new("L", mask.size, target_blue), mask)

    result = Image.merge(
        "RGB",
        (
            ImageChops.add(base_red, tint_red),
            ImageChops.add(base_green, tint_green),
            ImageChops.add(base_blue, tint_blue),
        ),
    )

    output = io.BytesIO()
    output.name = "derd.png"
    result.save(output, format="PNG", optimize=True, compress_level=7)
    output.seek(0)
    return output


if __name__ == "__main__":
    color = random_hex()
    preview = Path(__file__).with_name("preview.png")
    preview.write_bytes(render_cube(color).getvalue())
    print(f"Создан {preview.name}: {color}")
