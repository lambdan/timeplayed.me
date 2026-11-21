import hashlib
import io

import pytest
from PIL import Image

from tpbackend.files.images import (
    DISPLAY,
    PREVIEW,
    THUMBNAIL,
    ImageInfo,
    make_version,
)


def image_bytes(size: tuple[int, int], format="PNG", color=(200, 50, 50)) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, format=format)
    return out.getvalue()


def open_image(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))


class TestImageInfo:
    def test_png(self):
        data = image_bytes((60, 90))
        info = ImageInfo(data)
        assert info.content_type == "image/png"
        assert (info.width, info.height) == (60, 90)
        assert info.size == len(data)
        assert info.sha256 == hashlib.sha256(data).hexdigest()

    def test_jpeg(self):
        assert ImageInfo(image_bytes((60, 90), "JPEG")).content_type == "image/jpeg"

    def test_not_an_image(self):
        with pytest.raises(Exception):
            ImageInfo(b"<html>not found</html>")

    def test_unsupported_type(self):
        with pytest.raises(ValueError):
            ImageInfo(image_bytes((60, 90), "BMP"))


class TestMakeVersion:
    def test_display(self):
        display = open_image(make_version(image_bytes((1200, 1800)), DISPLAY))
        assert display.size == (600, 900)
        assert display.format == "WEBP"

    def test_thumbnail(self):
        thumbnail = open_image(make_version(image_bytes((1200, 1800)), THUMBNAIL))
        assert thumbnail.size == (120, 180)
        assert thumbnail.format == "WEBP"

    def test_preview(self):
        preview = open_image(make_version(image_bytes((600, 900)), PREVIEW))
        assert preview.size == (8, 12)
        assert preview.format == "PNG"
        assert preview.convert("RGB").getpixel((0, 0)) == (200, 50, 50)

    def test_keeps_aspect_ratio(self):
        display = open_image(make_version(image_bytes((2000, 1000)), DISPLAY))
        assert display.size == (600, 300)

    def test_never_enlarged(self):
        display = open_image(make_version(image_bytes((264, 374)), DISPLAY))
        assert display.size == (264, 374)

    def test_keeps_transparency(self):
        out = io.BytesIO()
        Image.new("RGBA", (10, 10), (0, 0, 0, 0)).save(out, format="PNG")
        display = open_image(make_version(out.getvalue(), DISPLAY))
        assert display.mode == "RGBA"
        assert display.getpixel((0, 0))[3] == 0
