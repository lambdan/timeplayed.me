import io

import pytest
from PIL import Image

from conftest import png_bytes
from tpbackend.storage import Game


@pytest.fixture
def admin(make_user):
    return make_user(name="admin", permissions=["admin"])


def upload(client, game, data: bytes):
    return client.put(
        f"/admin/game/{game.get_id()}/cover",
        data=data,
        headers={"Content-Type": "application/octet-stream"},
    )


class TestCoverUpload:
    def test_upload(self, admin, api, make_game):
        _, client = admin
        game = make_game(igdb_id=1234)
        r = upload(client, game, png_bytes())
        assert r.status_code == 200, r.text
        assert r.json()["uploaded_cover"]

        cover = api.get(f"/game/{game.get_id()}/cover").json()
        assert cover["source"] == "Uploaded"
        sizes = {
            "original": (600, 900),
            "display": (600, 900),
            "thumbnail": (120, 180),
            "preview": (8, 12),
        }
        assert cover["versions"].keys() == sizes.keys()
        assert cover["versions"]["original"]["content_type"] == "image/png"
        for version, size in sizes.items():
            listed = cover["versions"][version]
            assert (listed["width"], listed["height"]) == size
            r = api.get(f"/game/{game.get_id()}/cover/{version}", allow_redirects=False)
            assert r.status_code == 302, r.text
            location = r.headers["location"]
            assert location == listed["url"]
            r = api.get(location.removeprefix("/api"))
            assert r.status_code == 200
            assert Image.open(io.BytesIO(r.content)).size == size

    def test_used_by_children(self, admin, api, make_game):
        _, client = admin
        parent = make_game("Parent")
        child = make_game("Child", parent=parent)
        upload(client, parent, png_bytes())
        assert api.get(f"/game/{child.get_id()}/cover").json()["source"] == "Uploaded"

    def test_not_an_image(self, admin, make_game):
        _, client = admin
        r = upload(client, make_game(), b"<html>hi</html>")
        assert r.status_code == 400

    def test_remove(self, admin, api, make_game):
        _, client = admin
        game = make_game()
        upload(client, game, png_bytes())
        r = client.delete(f"/admin/game/{game.get_id()}/cover")
        assert r.status_code == 200
        assert r.json()["uploaded_cover"] is None
        assert api.get(f"/game/{game.get_id()}/cover").json()["source"] == "None"
        assert "Uploaded cover removed" in "\n".join(r.json()["history"])

    def test_url_that_fails(self, admin, make_game):
        _, client = admin
        r = client.put(
            f"/admin/game/{make_game().get_id()}/cover/url",
            json={"url": "https://example.invalid/cover.png"},
        )
        assert r.status_code == 400

    def test_requires_admin(self, make_user, make_game):
        _, client = make_user()
        assert upload(client, make_game(), png_bytes()).status_code == 403

    def test_nsfw_given_to_everyone(self, admin, api, make_game):
        # the site decides whether to show it
        _, client = admin
        game = make_game(nsfw=True)
        upload(client, game, png_bytes())
        r = api.get(f"/game/{game.get_id()}/cover/display", allow_redirects=False)
        assert r.status_code == 302

    def test_kept_when_merging(self, admin, make_game):
        _, client = admin
        source = make_game("Source")
        target = make_game("Target")
        upload(client, source, png_bytes())
        r = client.post(
            f"/admin/game/{source.get_id()}/merge",
            json={"into_game_id": target.get_id()},
        )
        assert r.status_code == 200, r.text
        assert Game.get_by_id(target.get_id()).get_uploaded_cover()
