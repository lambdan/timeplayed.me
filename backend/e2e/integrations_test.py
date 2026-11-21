"""
The e2e env runs without Discord and IGDB credentials, so these check that the
backend behaves when they are disabled.
"""

import pytest

from conftest import png_bytes
from tpbackend.storage import Game, GameCover


@pytest.fixture
def platform_id(make_platform):
    """the api requires a platform"""
    return make_platform("testplatform").get_id()


class TestCovers:
    def cover(self, api, game) -> dict:
        r = api.get(f"/game/{game.get_id()}/cover")
        assert r.status_code == 200, r.text
        return r.json()

    def image(self, api, game, version="display"):
        return api.get(f"/game/{game.get_id()}/cover/{version}", allow_redirects=False)

    def test_unknown_game(self, api):
        assert api.get("/game/999999/cover").status_code == 404
        assert api.get("/game/999999/cover/display").status_code == 404

    def test_no_cover(self, api, make_game):
        game = make_game()
        assert self.cover(api, game) == {
            "source": "None",
            "credits": None,
            "versions": {},
        }
        assert self.image(api, game).status_code == 404

    def test_unknown_version(self, api, make_game, upload_cover):
        game = make_game()
        upload_cover(game)
        assert self.image(api, game, "huge").status_code == 422

    def test_cached_for_a_while(self, api, make_game, upload_cover):
        game = make_game()
        upload_cover(game)
        r = self.image(api, game)
        assert r.headers["cache-control"] == "public, max-age=300"

    def test_disabled(self, api, make_game, upload_cover):
        game = make_game(cover_disabled=True)
        upload_cover(game)
        assert self.cover(api, game)["source"] == "Disabled"
        assert self.cover(api, game)["versions"] == {}
        assert self.image(api, game).status_code == 404

    def test_from_parent(self, api, make_game, upload_cover):
        parent = make_game("Parent")
        upload_cover(parent)
        child = make_game("Child", parent=parent)
        location = self.image(api, child).headers["location"]
        assert location == self.image(api, parent).headers["location"]

    def test_own_cover_before_parent(self, api, make_game, upload_cover):
        parent = make_game("Parent")
        child = make_game("Child", parent=parent)
        upload_cover(parent)
        upload_cover(child, png_bytes(color=(0, 0, 255)))
        location = self.image(api, child).headers["location"]
        assert location != self.image(api, parent).headers["location"]

    def test_igdb_without_integration_falls_through(self, api, make_game, upload_cover):
        # IGDB is disabled in e2e, so this finds nothing and the parent's is used
        parent = make_game("Parent")
        upload_cover(parent)
        child = make_game("Child", parent=parent, igdb_id=1234)
        assert self.cover(api, child)["source"] == "Uploaded"


class TestIGDBCovers:
    def test_stored_cover_without_asking_igdb(self, api, make_game, upload_cover):
        # an image to point to, IGDB is disabled in e2e so it can't be downloaded
        holder = make_game("Holder")
        upload_cover(holder)
        image = Game.get_by_id(holder.get_id()).get_uploaded_cover()

        game = make_game("On IGDB", igdb_id=1234)
        GameCover.create(
            game=game,
            image=image,
            source=GameCover.IGDB,
            igdb_id=1234,
        )
        cover = api.get(f"/game/{game.get_id()}/cover").json()
        assert cover["source"] == "IGDB"
        r = api.get(f"/game/{game.get_id()}/cover/display", allow_redirects=False)
        assert r.headers["location"].startswith("/api/files/")

    def test_igdb_id_changed(self, api, make_game, upload_cover):
        holder = make_game("Holder")
        upload_cover(holder)
        image = Game.get_by_id(holder.get_id()).get_uploaded_cover()
        game = make_game("On IGDB", igdb_id=5678)
        # stored for the IGDB ID the game had before
        GameCover.create(game=game, image=image, source=GameCover.IGDB, igdb_id=1234)
        # looked up again, IGDB is disabled in e2e so there's none
        assert api.get(f"/game/{game.get_id()}/cover").json()["source"] == "None"

    def test_not_stored_and_igdb_disabled(self, api, make_game):
        game = make_game("On IGDB", igdb_id=1234)
        assert api.get(f"/game/{game.get_id()}/cover").json()["source"] == "None"


class TestIGDBDisabled:
    def test_game_info_unavailable(self, make_user):
        _, client = make_user(name="admin", permissions=["admin"])
        assert client.get("/admin/igdb/game/1").status_code == 503

    def test_search_unavailable(self, make_user):
        _, client = make_user()
        assert client.get("/igdb/search", params={"q": "zelda"}).status_code == 503

    def test_search_needs_login(self, api):
        assert api.get("/igdb/search", params={"q": "zelda"}).status_code in (401, 403)

    def test_search_needs_manual_activity(self, make_user):
        # everything but manual_activity
        _, client = make_user(permissions=["commands", "oblivionis_sync"])
        assert client.get("/igdb/search", params={"q": "zelda"}).status_code == 403

    def test_game_by_igdb_id_not_in_db(self, api):
        assert api.get("/game_igdb/1234").status_code == 503

    def test_game_by_igdb_id_in_db(self, api, make_game):
        game = make_game(igdb_id=1234)
        r = api.get("/game_igdb/1234")
        assert r.status_code == 200
        assert r.json()["id"] == game.get_id()

    def test_add_activity_by_unknown_igdb_id(self, make_user, platform_id):
        _, client = make_user()
        r = client.post(
            "/activity",
            json={"platform_id": platform_id, "igdb_id": 1234, "seconds": 60},
        )
        assert r.status_code == 503

    def test_add_activity_by_unknown_steam_id(self, make_user, platform_id):
        _, client = make_user()
        r = client.post(
            "/activity",
            json={"platform_id": platform_id, "steam_id": 1234, "seconds": 60},
        )
        assert r.status_code == 503

    def test_add_activity_by_known_ids(self, make_user, make_game, platform_id):
        _, client = make_user()
        by_igdb = make_game("IGDB game", igdb_id=1234)
        by_steam = make_game("Steam game", steam_id=5678)

        r = client.post(
            "/activity",
            json={"platform_id": platform_id, "igdb_id": 1234, "seconds": 60},
        )
        assert r.status_code == 200, r.text
        assert r.json()["game_id"] == by_igdb.get_id()

        r = client.post(
            "/activity",
            json={"platform_id": platform_id, "steam_id": 5678, "seconds": 60},
        )
        assert r.status_code == 200, r.text
        assert r.json()["game_id"] == by_steam.get_id()

    def test_start_live_activity_by_unknown_igdb_id(self, make_user, platform_id):
        _, client = make_user()
        r = client.post(
            "/activity/live", json={"platform_id": platform_id, "igdb_id": 1234}
        )
        assert r.status_code == 503


class TestDiscordDisabled:
    def test_avatar_falls_back_to_default(self, api):
        r = api.get("/discord/1234/avatar", allow_redirects=False)
        assert r.status_code == 307
        assert r.headers["location"] == "https://cdn.discordapp.com/embed/avatars/4.png"
