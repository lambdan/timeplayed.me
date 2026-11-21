import hashlib
import io

import pytest
from PIL import Image

from tpbackend.files import images
from tpbackend.files.images import (
    DISPLAY,
    PREVIEW,
    THUMBNAIL,
    ImageInfo,
    get_versions,
    make_version,
)
from tpbackend.storage import ImageFile


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


class TestGetVersions:
    @pytest.fixture
    def made(self, monkeypatch) -> list[str]:
        """the versions that get made, none are stored yet"""
        names: list[str] = []

        def get_version(image, version):
            names.append(version.name)
            return ImageFile(width=1, height=1, version=version.name)

        monkeypatch.setattr(images, "stored_versions", lambda image: {})
        monkeypatch.setattr(images, "get_version", get_version)
        return names

    def test_large_image(self, made):
        image = ImageFile(content_type="image/jpeg", width=1200, height=1800)
        versions = get_versions(image)
        assert made == ["display", "thumbnail", "preview"]
        assert all(versions[name] is not image for name in made)

    def test_small_enough_to_be_the_display_version(self, made):
        # like IGDB's covers, 264x352
        image = ImageFile(content_type="image/jpeg", width=264, height=352)
        versions = get_versions(image)
        assert versions["display"] is image
        assert made == ["thumbnail", "preview"]

    def test_tiny_image_is_every_version(self, made):
        image = ImageFile(content_type="image/png", width=8, height=12)
        versions = get_versions(image)
        assert all(version is image for version in versions.values())
        assert made == []

    def test_gif_is_always_made(self, made):
        image = ImageFile(content_type="image/gif", width=264, height=352)
        get_versions(image)
        assert made == ["display", "thumbnail", "preview"]
