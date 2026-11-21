import hashlib
import io
import uuid
from pathlib import Path

from PIL import Image

from tpbackend.storage import ImageFile

# the backend's FILES_DIR, see docker-compose.yml
FILES_DIR = Path(__file__).parent / "files"


def make_image(data: bytes, store=True, **kwargs) -> ImageFile:
    image = ImageFile(
        content_type="image/png",
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        width=1,
        height=1,
        **kwargs,
    )
    image.save(force_insert=True)
    if store:
        path = FILES_DIR / image.get_id()[:2] / image.get_id()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return image


class TestFiles:
    def test_served(self, api):
        image = make_image(b"not really a png")
        r = api.get(f"/files/{image.get_id()}")
        assert r.status_code == 200
        assert r.content == b"not really a png"
        assert r.headers["content-type"] == "image/png"
        assert "immutable" in r.headers["cache-control"]

    def test_unknown(self, api):
        assert api.get(f"/files/{uuid.uuid4()}").status_code == 404

    def test_not_a_uuid(self, api):
        assert api.get("/files/..%2F..%2Fetc%2Fpasswd").status_code in (404, 422)

    def test_file_missing_and_no_source(self, api):
        image = make_image(b"gone", store=False)
        assert api.get(f"/files/{image.get_id()}").status_code == 404

    def test_file_missing_and_source_unreachable(self, api):
        image = make_image(b"gone", store=False, source="https://example.invalid/a.png")
        assert api.get(f"/files/{image.get_id()}").status_code == 404

    def test_display_version_made_again_from_original(self, api):
        out = io.BytesIO()
        Image.new("RGB", (1200, 1800), (200, 50, 50)).save(out, format="PNG")
        original = make_image(out.getvalue())
        display = make_image(
            b"gone", store=False, original=original.get_id(), version="display"
        )
        r = api.get(f"/files/{display.get_id()}")
        assert r.status_code == 200
        remade = Image.open(io.BytesIO(r.content))
        assert remade.format == "WEBP"
        assert remade.size == (600, 900)
