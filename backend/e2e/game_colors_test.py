import pytest

from tpbackend.storage import Game


@pytest.fixture
def admin(make_user):
    _, client = make_user(name="admin", permissions=["admin"])
    return client


def colors(api, game: Game) -> tuple[str | None, str | None]:
    data = api.get(f"/game/{game.get_id()}").json()
    return data["color_primary"], data["color_secondary"]


class TestGameColors:
    def test_none_by_default(self, api, make_game):
        assert colors(api, make_game()) == (None, None)

    def test_set_by_admin(self, admin, api, make_game):
        game = make_game()
        r = admin.patch(
            f"/admin/game/{game.get_id()}",
            json={"color_primary": "#1A2B3C", "color_secondary": "ffffff"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["own_color_primary"] == "1a2b3c"
        assert colors(api, game) == ("1a2b3c", "ffffff")
        messages = [h["message"] for h in r.json()["history"]]
        assert "Primary color changed from 'None' to '1a2b3c'" in messages

        r = admin.patch(f"/admin/game/{game.get_id()}", json={"color_primary": None})
        assert r.json()["own_color_primary"] is None
        assert colors(api, game) == (None, "ffffff")

    def test_not_a_color(self, admin, make_game):
        game = make_game()
        r = admin.patch(f"/admin/game/{game.get_id()}", json={"color_primary": "red"})
        assert r.status_code == 400

    def test_in_game_lists(self, api, make_game):
        make_game(color_primary="1a2b3c", color_secondary="ffffff")
        games = api.get("/games").json()
        assert [(g["color_primary"], g["color_secondary"]) for g in games] == [
            ("1a2b3c", "ffffff")
        ]

    def test_children_get_the_parents(self, admin, api, make_game):
        parent = make_game("Parent", color_primary="1a2b3c", color_secondary="ffffff")
        child = make_game("Child", parent=parent)
        assert colors(api, child) == ("1a2b3c", "ffffff")
        # but only the game's own in admin, that's what can be changed
        r = admin.get(f"/admin/game/{child.get_id()}")
        assert r.json()["own_color_primary"] is None

    def test_child_with_its_own(self, api, make_game):
        parent = make_game("Parent", color_primary="1a2b3c", color_secondary="ffffff")
        child = make_game("Child", parent=parent, color_primary="f5e614")
        # not mixed with the parent's secondary
        assert colors(api, child) == ("f5e614", None)


class TestCoverColors:
    def test_picked_from_cover(self, admin, make_game, upload_cover):
        game = make_game()
        upload_cover(game)  # (200, 50, 50)
        r = admin.get(f"/admin/game/{game.get_id()}/cover/colors")
        assert r.status_code == 200, r.text
        assert r.json() == {"color_primary": "c83232", "color_secondary": "ffffff"}
        # nothing is saved, the admin sets them
        assert Game.get_by_id(game.get_id()).get_color_primary() is None

    def test_parents_cover(self, admin, make_game, upload_cover):
        parent = make_game("Parent")
        child = make_game("Child", parent=parent)
        upload_cover(parent)
        r = admin.get(f"/admin/game/{child.get_id()}/cover/colors")
        assert r.json()["color_primary"] == "c83232"

    def test_no_cover(self, admin, make_game):
        r = admin.get(f"/admin/game/{make_game().get_id()}/cover/colors")
        assert r.status_code == 404

    def test_admins_only(self, make_user, make_game):
        _, user = make_user(name="not admin")
        r = user.get(f"/admin/game/{make_game().get_id()}/cover/colors")
        assert r.status_code in (401, 403)
