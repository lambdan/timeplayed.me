import io

import pytest

from PIL import Image, ImageDraw

from tpbackend.files.colors import parse_color, pick_colors, text_color


def image_bytes(image: Image.Image) -> bytes:
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def two_colors(background, stripe, stripe_share: float) -> bytes:
    """background with a stripe covering stripe_share of the image"""
    # the size colors are picked at, so it's not resized and the colors don't blend
    image = Image.new("RGB", (64, 64), background)
    ImageDraw.Draw(image).rectangle([0, 0, 63, int(64 * stripe_share) - 1], stripe)
    return image_bytes(image)


def best_color(data: bytes) -> str:
    return pick_colors(data)[0]


class TestPickColors:
    def test_all_colors_best_first(self):
        colors = pick_colors(two_colors((120, 120, 120), (30, 90, 200), 0.3))
        assert colors == ["1e5ac8", "787878"]

    def test_vivid_by_score_then_others_by_share(self):
        image = Image.new("RGB", (64, 64), (120, 120, 120))
        draw = ImageDraw.Draw(image)
        # red covers more than blue, so it scores higher
        draw.rectangle([0, 0, 63, 19], (200, 30, 30))
        draw.rectangle([0, 20, 63, 29], (30, 30, 200))
        draw.rectangle([0, 30, 63, 33], (250, 250, 250))
        assert pick_colors(image_bytes(image)) == [
            "c81e1e",
            "1e1ec8",
            "787878",
            "fafafa",
        ]

    def test_one_color(self):
        assert (
            best_color(image_bytes(Image.new("RGB", (60, 90), (200, 50, 50))))
            == "c83232"
        )

    def test_vivid_wins_over_more_common_grey(self):
        assert best_color(two_colors((120, 120, 120), (30, 90, 200), 0.3)) == "1e5ac8"

    def test_vivid_wins_over_more_common_black(self):
        assert best_color(two_colors((5, 5, 5), (220, 180, 20), 0.3)) == "dcb414"

    def test_tiny_vivid_part_is_not_picked(self):
        # like small colored text on a grey cover
        assert best_color(two_colors((120, 120, 120), (255, 0, 0), 0.02)) == "787878"

    def test_grey_cover_not_white(self):
        # nothing vivid, the most common color that isn't near white
        assert best_color(two_colors((250, 250, 250), (60, 60, 60), 0.3)) == "3c3c3c"

    def test_white_cover(self):
        assert best_color(image_bytes(Image.new("RGB", (60, 90), "white"))) == "ffffff"

    def test_transparent_png(self):
        image = Image.new("RGBA", (60, 90), (30, 90, 200, 255))
        assert best_color(image_bytes(image)) == "1e5ac8"


class TestTextColor:
    def test_dark_background(self):
        assert text_color("1e5ac8") == "ffffff"

    def test_light_background(self):
        assert text_color("f5e614") == "000000"

    def test_bright_cyan_gets_black(self):
        assert text_color("00c0e0") == "000000"


class TestParseColor:
    def test_hash_and_case(self):
        assert parse_color(" #1A2B3C ") == "1a2b3c"

    def test_empty(self):
        assert parse_color(None) is None
        assert parse_color("") is None
        assert parse_color("#") is None

    def test_not_a_color(self):
        for color in ("red", "#12345", "1234567", "#gggggg"):
            with pytest.raises(ValueError):
                parse_color(color)
