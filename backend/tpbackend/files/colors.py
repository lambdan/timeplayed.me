"""
Colors picked from an image, for tiles (like a game's, from its cover)
"""

import colorsys
import io
import re

from PIL import Image

# the image is shrunk to this and reduced to this many colors first
SAMPLE_SIZE = (64, 64)
PALETTE_SIZE = 8
# colors covering less of the image than this aren't picked, like small text
MIN_SHARE = 0.05
# below this score nothing stands out, then it's the most common color
MIN_SCORE = 0.02
# colors closer than this (in RGB) look the same, only the better one is listed
MIN_DISTANCE = 40


def distance(a: tuple[int, ...], b: tuple[int, ...]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def is_near_white(rgb: tuple[int, ...]) -> bool:
    _, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    return v > 0.9 and s < 0.1


def pick_colors(data: bytes) -> list[str]:
    """
    the image's colors as hex without #, best first. The best is its most striking color:
    common and vivid, not near black. Images without one (like a grey or black cover) get
    their most common colors first, near white last so tiles don't disappear on the page
    """
    with Image.open(io.BytesIO(data)) as image:
        small = image.convert("RGB")
        small.thumbnail(SAMPLE_SIZE)
    quantized = small.quantize(colors=PALETTE_SIZE, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette() or []
    # (count, palette index), most common first
    counts = sorted(quantized.getcolors() or [], reverse=True)
    total = sum(count for count, _ in counts)

    vivid: list[tuple[float, tuple[int, ...]]] = []
    others: list[tuple[int, ...]] = []
    for count, i in counts:
        share = count / total
        rgb = tuple(palette[i * 3 : i * 3 + 3])
        _, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
        # vivid wins, dark colors count for less
        score = share * s * min(1, v / 0.4)
        if share >= MIN_SHARE and score >= MIN_SCORE:
            vivid.append((score, rgb))
        else:
            others.append(rgb)

    vivid.sort(key=lambda scored: scored[0], reverse=True)
    # others stay most common first, near white ones go last (sort is stable)
    others.sort(key=is_near_white)
    ranked = [rgb for _, rgb in vivid] + others

    # reducing colors gives near copies, like two blues for one blue area
    picked: list[tuple[int, ...]] = []
    for rgb in ranked:
        if not any(distance(rgb, other) < MIN_DISTANCE for other in picked):
            picked.append(rgb)
    return ["%02x%02x%02x" % rgb for rgb in picked]


def text_color(background: str) -> str:
    """black or white, whichever is easier to read on the background (WCAG contrast)"""

    def linear(i: int) -> float:
        c = int(background[i : i + 2], 16) / 255
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    luminance = 0.2126 * linear(0) + 0.7152 * linear(2) + 0.0722 * linear(4)
    on_white = 1.05 / (luminance + 0.05)
    on_black = (luminance + 0.05) / 0.05
    if on_white > on_black:
        return "ffffff"
    return "000000"


def parse_color(color: str | None) -> str | None:
    """
    a color from an admin, as stored: hex without #, lowercase. None for empty.
    ValueError if it isn't a hex color
    """
    if color is None:
        return None
    color = color.strip().lstrip("#").lower()
    if not color:
        return None
    if not re.fullmatch("[0-9a-f]{6}", color):
        raise ValueError("must be a hex color like #1a2b3c")
    return color
