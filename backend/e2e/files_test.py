import hashlib
import uuid


from tpbackend.storage import ImageFile, ImageFileData


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
        ImageFileData.create(file=image.get_id(), data=data)
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

    def test_bytes_missing(self, api):
        image = make_image(b"gone", store=False)
        assert api.get(f"/files/{image.get_id()}").status_code == 404

    def test_bytes_removed_with_the_file(self, api):
        image = make_image(b"hello")
        image.delete_instance()
        assert ImageFileData.get_or_none(ImageFileData.file == image.get_id()) is None
