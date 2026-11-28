import io

from PIL import Image, ImageDraw

from tpbackend.files.colors import pick_color, text_color


def image_bytes(image: Image.Image) -> bytes:
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def two_colors(background, stripe, stripe_share: float) -> bytes:
    """background with a stripe covering stripe_share of the image"""
    image = Image.new("RGB", (100, 100), background)
    ImageDraw.Draw(image).rectangle([0, 0, 99, int(100 * stripe_share) - 1], stripe)
    return image_bytes(image)


class TestPickColor:
    def test_one_color(self):
        assert (
            pick_color(image_bytes(Image.new("RGB", (60, 90), (200, 50, 50))))
            == "c83232"
        )

    def test_vivid_wins_over_more_common_grey(self):
        assert pick_color(two_colors((120, 120, 120), (30, 90, 200), 0.3)) == "1e5ac8"

    def test_vivid_wins_over_more_common_black(self):
        assert pick_color(two_colors((5, 5, 5), (220, 180, 20), 0.3)) == "dcb414"

    def test_tiny_vivid_part_is_not_picked(self):
        # like small colored text on a grey cover
        assert pick_color(two_colors((120, 120, 120), (255, 0, 0), 0.02)) == "787878"

    def test_grey_cover_not_white(self):
        # nothing vivid, the most common color that isn't near white
        assert pick_color(two_colors((250, 250, 250), (60, 60, 60), 0.3)) == "3c3c3c"

    def test_white_cover(self):
        assert pick_color(image_bytes(Image.new("RGB", (60, 90), "white"))) == "ffffff"

    def test_transparent_png(self):
        image = Image.new("RGBA", (60, 90), (30, 90, 200, 255))
        assert pick_color(image_bytes(image)) == "1e5ac8"


class TestTextColor:
    def test_dark_background(self):
        assert text_color("1e5ac8") == "ffffff"

    def test_light_background(self):
        assert text_color("f5e614") == "000000"

    def test_bright_cyan_gets_black(self):
        assert text_color("00c0e0") == "000000"
