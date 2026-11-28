"""
Colors picked from an image, for tiles (like a game's, from its cover)
"""

import colorsys
import io

from PIL import Image

# the image is shrunk to this and reduced to this many colors first
SAMPLE_SIZE = (64, 64)
PALETTE_SIZE = 8
# colors covering less of the image than this aren't picked, like small text
MIN_SHARE = 0.05
# below this score nothing stands out, then it's the most common color
MIN_SCORE = 0.02


def is_near_white(rgb: tuple[int, ...]) -> bool:
    _, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    return v > 0.9 and s < 0.1


def pick_color(data: bytes) -> str:
    """
    the image's most striking color, as hex without #: common and vivid, not near black.
    Images without one (like a grey or black cover) get their most common color,
    not near white so tiles don't disappear on the page
    """
    with Image.open(io.BytesIO(data)) as image:
        small = image.convert("RGB")
        small.thumbnail(SAMPLE_SIZE)
    quantized = small.quantize(colors=PALETTE_SIZE, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette() or []
    # (count, palette index), most common first
    counts = sorted(quantized.getcolors() or [], reverse=True)
    total = sum(count for count, _ in counts)
    colors = [(count / total, tuple(palette[i * 3 : i * 3 + 3])) for count, i in counts]

    best = None
    best_score = 0.0
    for share, rgb in colors:
        if share < MIN_SHARE:
            continue
        _, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
        # vivid wins, dark colors count for less
        score = share * s * min(1, v / 0.4)
        if score > best_score:
            best, best_score = rgb, score

    if best is None or best_score < MIN_SCORE:
        not_white = [rgb for _, rgb in colors if not is_near_white(rgb)]
        if not_white:
            best = not_white[0]
        else:
            best = colors[0][1]
    return "%02x%02x%02x" % best


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
