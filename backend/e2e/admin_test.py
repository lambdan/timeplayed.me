import datetime

import pytest

from tpbackend.storage import Activity, DiscordHistory, Game, Platform, User

UTC = datetime.timezone.utc


def add_activity(user, game, platform, seconds=3600, ended=None, **kwargs):
    return Activity.create(
        user=user,
        game=game,
        platform=platform,
        seconds=seconds,
        timestamp=ended or datetime.datetime.now(UTC),
        **kwargs,
    )


@pytest.fixture
def admin(make_user):
    """(user, client) with admin permission"""
    return make_user(name="admin", permissions=["commands", "admin"])


class TestAdminAuth:
    def test_requires_token(self, api):
        assert api.get("/admin/users").status_code in (401, 403)

    def test_requires_admin(self, make_user):
        _, client = make_user(name="regular")
        assert client.get("/admin/users").status_code == 403
        assert client.delete("/admin/user/1").status_code == 403

    def test_not_in_openapi(self, api):
        paths = api.get("/openapi.json").json()["paths"]
        assert not [p for p in paths if p.startswith("/admin")]


class TestAdminUsers:
    def test_list(self, admin, make_user):
        _, client = admin
        make_user(name="bob")
        r = client.get("/admin/users")
        assert r.status_code == 200, r.text
        assert [u["name"] for u in r.json()] == ["admin", "bob"]
        assert r.json()[0]["permissions"] == ["commands", "admin"]

    def test_set_permissions(self, admin, make_user):
        _, client = admin
        bob, _ = make_user(name="bob")
        r = client.put(
            f"/admin/user/{bob.get_id()}/permissions",
            json={"permissions": ["commands", "developer"]},
        )
        assert r.status_code == 200, r.text
        assert User.get_by_id(bob.get_id()).get_permissions() == [
            "commands",
            "developer",
        ]
        assert any("Added permission 'developer'" in h for h in r.json()["history"])

    def test_set_invalid_permission(self, admin, make_user):
        _, client = admin
        bob, _ = make_user(name="bob")
        r = client.put(
            f"/admin/user/{bob.get_id()}/permissions",
            json={"permissions": ["superuser"]},
        )
        assert r.status_code == 400

    def test_cant_remove_own_admin(self, admin):
        user, client = admin
        r = client.put(
            f"/admin/user/{user.get_id()}/permissions",
            json={"permissions": ["commands"]},
        )
        assert r.status_code == 400
        assert User.get_by_id(user.get_id()).has_permission("admin")

    def test_delete(self, admin, make_user, make_game, make_platform):
        _, client = admin
        bob, _ = make_user(name="bob")
        add_activity(bob, make_game(), make_platform())
        r = client.delete(f"/admin/user/{bob.get_id()}")
        assert r.status_code == 200, r.text
        assert User.get_or_none(User.id == bob.get_id()) is None
        assert Activity.select().count() == 0

    def test_cant_delete_self(self, admin):
        user, client = admin
        assert client.delete(f"/admin/user/{user.get_id()}").status_code == 400

    def test_discord_history(self, admin, make_user):
        _, client = admin
        bob, _ = make_user(name="bob", discord_id="555")
        DiscordHistory.create(event="received_message", user="555", message="!last")
        DiscordHistory.create(event="received_message", user="666", message="!help")
        r = client.get(f"/admin/user/{bob.get_id()}/discord_history")
        assert r.status_code == 200, r.text
        assert [e["message"] for e in r.json()] == ["!last"]


class TestAdminActivities:
    def test_list_includes_hidden(self, admin, make_game, make_platform):
        user, client = admin
        game = make_game()
        add_activity(user, game, make_platform(), hidden=True)
        r = client.get(f"/admin/activities?game={game.get_id()}")
        assert r.status_code == 200, r.text
        assert len(r.json()) == 1
        assert r.json()[0]["hidden"] is True

    def test_patch(self, admin, make_user, make_game, make_platform):
        _, client = admin
        bob, _ = make_user(name="bob")
        old_game = make_game("Old")
        new_game = make_game("New")
        activity = add_activity(bob, old_game, make_platform())
        ended = datetime.datetime(2026, 1, 1, 12, tzinfo=UTC)

        r = client.patch(
            f"/admin/activity/{activity.get_id()}",
            json={
                "game_id": new_game.get_id(),
                "seconds": 600,
                "ended": int(ended.timestamp() * 1000),
            },
        )
        assert r.status_code == 200, r.text
        activity = Activity.get_by_id(activity.get_id())
        assert activity.get_game() == new_game
        assert activity.get_seconds() == 600
        assert activity.get_ended() == ended
        assert any("Edited by admin admin" in h for h in activity.get_history())

    def test_patch_too_short(self, admin, make_game, make_platform):
        user, client = admin
        activity = add_activity(user, make_game(), make_platform())
        r = client.patch(f"/admin/activity/{activity.get_id()}", json={"seconds": 0})
        assert r.status_code == 400

    def test_delete_any_users_activity(
        self, admin, make_user, make_game, make_platform
    ):
        _, client = admin
        bob, _ = make_user(name="bob")
        activity = add_activity(bob, make_game(), make_platform())
        r = client.delete(f"/admin/activity/{activity.get_id()}")
        assert r.status_code == 200, r.text
        assert Activity.select().count() == 0

    def test_move(self, admin, make_user, make_game, make_platform):
        user, client = admin
        bob, _ = make_user(name="bob")
        source = make_game("Source")
        target = make_game("Target")
        pc = make_platform()
        add_activity(user, source, pc)
        add_activity(bob, source, pc)
        r = client.post(
            "/admin/activities/move",
            json={"from_game_id": source.get_id(), "to_game_id": target.get_id()},
        )
        assert r.status_code == 200, r.text
        assert r.json()["moved"] == 2
        assert Activity.select().where(Activity.game == target).count() == 2
        # unlike merge, the source game is kept
        assert Game.get_or_none(Game.id == source.get_id()) is not None

    def test_overlaps(self, admin, make_game, make_platform):
        user, client = admin
        game = make_game()
        pc = make_platform()
        ended = datetime.datetime(2026, 1, 1, 12, tzinfo=UTC)
        long = add_activity(user, game, pc, seconds=3600, ended=ended)
        short = add_activity(user, game, pc, seconds=600, ended=ended)

        r = client.get("/admin/activities/overlaps")
        assert r.status_code == 200, r.text
        assert r.json() == [{"keep_id": long.get_id(), "remove_ids": [short.get_id()]}]

        r = client.post("/admin/activities/overlaps/merge")
        assert r.status_code == 200, r.text
        assert r.json() == {"groups": 1, "removed": 1}
        assert [a.get_id() for a in Activity.select()] == [long.get_id()]


class TestAdminGames:
    def test_add(self, admin):
        _, client = admin
        r = client.post("/admin/game", json={"name": "New Game"})
        assert r.status_code == 200, r.text
        assert Game.get_by_id(r.json()["id"]).get_name() == "New Game"

    def test_add_duplicate(self, admin, make_game):
        _, client = admin
        make_game("New Game")
        assert client.post("/admin/game", json={"name": "New Game"}).status_code == 400

    def test_get_includes_hidden(self, admin, make_game):
        _, client = admin
        game = make_game(hidden=True)
        r = client.get(f"/admin/game/{game.get_id()}")
        assert r.status_code == 200, r.text
        assert r.json()["hidden"] is True

    def test_patch(self, admin, make_game):
        _, client = admin
        parent = make_game("Parent")
        game = make_game("Old name", image_url="http://x/old.png")
        r = client.patch(
            f"/admin/game/{game.get_id()}",
            json={
                "name": "New name",
                "release_year": 2001,
                "image_url": None,
                "parent_id": parent.get_id(),
            },
        )
        assert r.status_code == 200, r.text
        game = Game.get_by_id(game.get_id())
        assert game.get_name() == "New name"
        assert game.get_release_year() == 2001
        assert game.image_url is None
        assert game.get_parent() == parent

    def test_patch_unsent_fields_unchanged(self, admin, make_game):
        _, client = admin
        game = make_game("Name", release_year=1999, image_url="http://x/a.png")
        r = client.patch(f"/admin/game/{game.get_id()}", json={"name": "Other"})
        assert r.status_code == 200, r.text
        game = Game.get_by_id(game.get_id())
        assert game.get_release_year() == 1999
        assert game.image_url == "http://x/a.png"

    def test_patch_name_and_year_conflict(self, admin, make_game):
        _, client = admin
        make_game("Resident Evil 2", release_year=1998)
        game = make_game("Resident Evil 2", release_year=2019)
        r = client.patch(f"/admin/game/{game.get_id()}", json={"release_year": 1998})
        assert r.status_code == 400
        assert Game.get_by_id(game.get_id()).get_release_year() == 2019

    def test_hide_hides_activities(self, admin, make_game, make_platform):
        user, client = admin
        game = make_game()
        add_activity(user, game, make_platform())
        r = client.patch(f"/admin/game/{game.get_id()}", json={"hidden": True})
        assert r.status_code == 200, r.text
        assert Game.get_by_id(game.get_id()).get_hidden() is True
        assert Activity.get().get_hidden() is True

    def test_clear_igdb_id(self, admin, make_game):
        _, client = admin
        game = make_game(igdb_id=123)
        r = client.put(f"/admin/game/{game.get_id()}/igdb", json={"igdb_id": None})
        assert r.status_code == 200, r.text
        assert Game.get_by_id(game.get_id()).igdb_id is None

    def test_igdb_id_taken(self, admin, make_game):
        _, client = admin
        make_game("Other", igdb_id=123)
        game = make_game()
        r = client.put(f"/admin/game/{game.get_id()}/igdb", json={"igdb_id": 123})
        assert r.status_code == 400
        assert "merge" in r.json()["detail"]

    def test_sgdb_zero(self, admin, make_game):
        _, client = admin
        make_game("Other", sgdb_id=0)
        game = make_game()
        r = client.put(f"/admin/game/{game.get_id()}/sgdb", json={"sgdb_id": 0})
        assert r.status_code == 200, r.text
        assert Game.get_by_id(game.get_id()).sgdb_id == 0

    def test_aliases(self, admin, make_game):
        _, client = admin
        make_game("Taken")
        game = make_game()
        r = client.post(f"/admin/game/{game.get_id()}/aliases", json={"alias": "Bla"})
        assert r.status_code == 200, r.text
        assert r.json()["aliases"] == ["Bla"]

        r = client.post(f"/admin/game/{game.get_id()}/aliases", json={"alias": "Taken"})
        assert r.status_code == 400

        r = client.delete(f"/admin/game/{game.get_id()}/aliases?alias=Bla")
        assert r.status_code == 200, r.text
        assert Game.get_by_id(game.get_id()).get_aliases() == []

    def test_delete(self, admin, make_game):
        _, client = admin
        game = make_game()
        assert client.delete(f"/admin/game/{game.get_id()}").status_code == 200
        assert Game.get_or_none(Game.id == game.get_id()) is None

    def test_delete_with_activities(self, admin, make_game, make_platform):
        user, client = admin
        game = make_game()
        add_activity(user, game, make_platform())
        assert client.delete(f"/admin/game/{game.get_id()}").status_code == 400

    def test_merge(self, admin, make_game, make_platform):
        user, client = admin
        source = make_game("Bla™")
        target = make_game("Bla")
        add_activity(user, source, make_platform())

        r = client.get(f"/admin/game/{source.get_id()}/merge?into={target.get_id()}")
        assert r.status_code == 200, r.text
        assert r.json() == {"activity_count": 1, "new_aliases": ["Bla™"]}

        r = client.post(
            f"/admin/game/{source.get_id()}/merge",
            json={"into_game_id": target.get_id()},
        )
        assert r.status_code == 200, r.text
        assert r.json()["moved"] == 1
        assert Game.get_or_none(Game.id == source.get_id()) is None
        assert Activity.get().get_game() == target

    def test_missing(self, admin, make_game):
        _, client = admin
        make_game("Has IGDB", igdb_id=1)
        missing = make_game("No IGDB")
        r = client.get("/admin/games?missing=igdb")
        assert r.status_code == 200, r.text
        assert [g["id"] for g in r.json()] == [missing.get_id()]


class TestAdminPlatforms:
    def test_add(self, admin):
        _, client = admin
        r = client.post("/admin/platform", json={"abbreviation": "PS6"})
        assert r.status_code == 200, r.text
        assert r.json()["abbreviation"] == "ps6"

    def test_patch(self, admin, make_platform):
        _, client = admin
        platform = make_platform("ps5", icon="playstation")
        r = client.patch(
            f"/admin/platform/{platform.get_id()}",
            json={"name": "PlayStation 5", "color_primary": "#003791", "icon": None},
        )
        assert r.status_code == 200, r.text
        platform = Platform.get_by_id(platform.get_id())
        assert platform.get_name() == "PlayStation 5"
        assert platform.get_color_primary() == "003791"
        assert platform.get_icon() is None

    def test_delete(self, admin, make_platform):
        _, client = admin
        platform = make_platform("ps6")
        assert client.delete(f"/admin/platform/{platform.get_id()}").status_code == 200
        assert Platform.get_or_none(Platform.id == platform.get_id()) is None

    def test_delete_with_activities(self, admin, make_game, make_platform):
        user, client = admin
        platform = make_platform("ps6")
        add_activity(user, make_game(), platform)
        r = client.delete(f"/admin/platform/{platform.get_id()}")
        assert r.status_code == 400
