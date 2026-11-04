import datetime

import pytest

from conftest import Api
from tpbackend.permissions import DEFAULT_PERMISSIONS, DESCRIPTIONS, Permission
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

    def test_permissions_have_descriptions(self, admin):
        _, client = admin
        r = client.get("/admin/permissions")
        assert r.status_code == 200, r.text
        admin_permission = next(p for p in r.json() if p["name"] == "admin")
        assert admin_permission["description"] == DESCRIPTIONS[Permission.ADMIN]

    def test_add(self, admin):
        _, client = admin
        r = client.post("/admin/user", json={"name": "test", "display_name": "Test"})
        assert r.status_code == 200, r.text
        user = User.get_by_id(r.json()["id"])
        assert user.get_name() == "test"
        assert user.get_display_name() == "Test"
        assert user.get_discord_id() is None
        assert user.get_permissions() == DEFAULT_PERMISSIONS
        assert any("User added by admin admin" in h for h in r.json()["history"])

    def test_add_empty_name(self, admin):
        _, client = admin
        assert client.post("/admin/user", json={"name": " "}).status_code == 400

    def test_token(self, admin, make_user):
        _, client = admin
        bob, _ = make_user(name="bob")
        r = client.post(f"/admin/user/{bob.get_id()}/token")
        assert r.status_code == 200, r.text
        token = r.json()["token"]
        # the token works as bob
        r = Api(token).get("/who_am_i")
        assert r.status_code == 200
        assert r.json()["id"] == bob.get_id()
        history = User.get_by_id(bob.get_id()).get_history()
        assert any(f"Token {token[:4]}...{token[-4:]}" in h for h in history)
        assert not any(token in h for h in history)

    def test_list_tokens(self, admin, make_user):
        user, client = admin
        bob, _ = make_user(name="bob")
        client.post(f"/admin/user/{bob.get_id()}/token")
        r = client.get(f"/admin/user/{bob.get_id()}/tokens")
        assert r.status_code == 200, r.text
        # make_user gave bob one token, the admin made another
        assert len(r.json()) == 2
        assert not any(t["current"] for t in r.json())
        # the admins own session is marked
        r = client.get(f"/admin/user/{user.get_id()}/tokens")
        assert [t["current"] for t in r.json()] == [True]

    def test_revoke_token(self, admin, make_user):
        _, client = admin
        bob, bob_client = make_user(name="bob")
        token_id = client.get(f"/admin/user/{bob.get_id()}/tokens").json()[0]["id"]
        r = client.delete(f"/admin/user/{bob.get_id()}/tokens/{token_id}")
        assert r.status_code == 200, r.text
        assert bob_client.get("/who_am_i").status_code == 401
        history = User.get_by_id(bob.get_id()).get_history()
        assert any(f"Token {token_id} revoked by admin admin" in h for h in history)

    def test_revoke_token_of_other_user(self, admin, make_user):
        _, client = admin
        bob, _ = make_user(name="bob")
        alice, alice_client = make_user(name="alice")
        token_id = client.get(f"/admin/user/{alice.get_id()}/tokens").json()[0]["id"]
        # the token has to belong to the user in the url
        r = client.delete(f"/admin/user/{bob.get_id()}/tokens/{token_id}")
        assert r.status_code == 404
        assert alice_client.get("/who_am_i").status_code == 200

    def test_revoke_all_tokens(self, admin, make_user):
        _, client = admin
        bob, bob_client = make_user(name="bob")
        client.post(f"/admin/user/{bob.get_id()}/token")
        r = client.delete(f"/admin/user/{bob.get_id()}/tokens")
        assert r.status_code == 200, r.text
        assert r.json() == "Revoked 2 tokens"
        assert bob_client.get("/who_am_i").status_code == 401

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

    def test_sorted_by_last_played(self, admin, make_game, make_platform):
        user, client = admin
        pc = make_platform()
        old = make_game("Old")
        new = make_game("New")
        hidden = make_game("Hidden", hidden=True)
        never = make_game("Never played")
        never_newer = make_game("Never played, newer")
        add_activity(user, old, pc, ended=datetime.datetime(2025, 1, 1, tzinfo=UTC))
        add_activity(user, new, pc, ended=datetime.datetime(2026, 1, 1, tzinfo=UTC))
        # hidden activities count in admin
        add_activity(
            user,
            hidden,
            pc,
            ended=datetime.datetime(2025, 6, 1, tzinfo=UTC),
            hidden=True,
        )

        r = client.get("/admin/games")
        assert r.status_code == 200, r.text
        assert [g["name"] for g in r.json()] == [
            "New",
            "Hidden",
            "Old",
            "Never played, newer",
            "Never played",
        ]
        assert r.json()[0]["last_activity"] == int(
            datetime.datetime(2026, 1, 1, tzinfo=UTC).timestamp() * 1000
        )
        assert r.json()[-1]["last_activity"] is None

    def test_missing_cover_leaves_out_not_on_igdb(self, admin, make_game):
        _, client = admin
        make_game("Has cover", igdb_id=1)
        missing = make_game("No cover")
        not_on_igdb = make_game("Not on IGDB", igdb_id=0)
        # got a cover another way, not listed anymore
        make_game("Not on IGDB, has image", igdb_id=0, image_url="http://x/a.png")

        r = client.get("/admin/games?missing=cover")
        assert r.status_code == 200, r.text
        assert [g["id"] for g in r.json()] == [missing.get_id()]

        r = client.get("/admin/games?missing=not_on_igdb")
        assert r.status_code == 200, r.text
        assert [g["id"] for g in r.json()] == [not_on_igdb.get_id()]

    def test_mark_not_on_igdb(self, admin, make_game):
        _, client = admin
        game = make_game()
        r = client.put(f"/admin/game/{game.get_id()}/igdb", json={"igdb_id": 0})
        assert r.status_code == 200, r.text
        assert Game.get_by_id(game.get_id()).igdb_id == 0

    def test_missing(self, admin, make_game):
        _, client = admin
        make_game("Has IGDB", igdb_id=1)
        missing = make_game("No IGDB")
        r = client.get("/admin/games?missing=igdb")
        assert r.status_code == 200, r.text
        assert [g["id"] for g in r.json()] == [missing.get_id()]


class TestAdminPlatforms:
    def test_sorted_by_last_played(self, admin, make_game, make_platform):
        user, client = admin
        game = make_game()
        old = make_platform("old")
        new = make_platform("new")
        make_platform("never")
        add_activity(user, game, old, ended=datetime.datetime(2025, 1, 1, tzinfo=UTC))
        add_activity(user, game, new, ended=datetime.datetime(2026, 1, 1, tzinfo=UTC))

        r = client.get("/admin/platforms")
        assert r.status_code == 200, r.text
        names = [p["abbreviation"] for p in r.json()]
        # "unknown" is created for the admins default platform, also never played
        assert names[:2] == ["new", "old"]
        assert set(names[2:]) == {"never", "unknown"}

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
