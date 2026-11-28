import datetime

import pytest

from tpbackend.discord import controller
from tpbackend.discord.bot import default_avatar_url
from tpbackend.operations import add_session
from tpbackend.permissions import DEFAULT_PERMISSIONS, Permission
from tpbackend.storage import LiveActivity, User
from tpbackend.utils2 import now


def with_permission(*permissions: Permission) -> list[str]:
    return [*DEFAULT_PERMISSIONS, *permissions]


def play(user, game, platform, seconds=3600, hours_ago=1):
    """an activity that ended hours_ago, so several don't overlap"""
    timestamp = now() - datetime.timedelta(hours=hours_ago)
    activity, error = add_session(
        user=user, game=game, seconds=seconds, platform=platform, timestamp=timestamp
    )
    assert error is None
    return activity


class TestAnonymous:
    def test_shown_by_default(self, api, make_user):
        user, _ = make_user(name="alice", display_name="Alice", discord_id="1234")
        r = api.get(f"/user/{user.get_id()}")
        assert r.status_code == 200
        assert r.json()["name"] == "alice"
        assert r.json()["display_name"] == "Alice"
        assert r.json()["discord_id"] == "1234"

    @pytest.mark.parametrize(
        "permission", [Permission.ANONYMOUS, Permission.FORCE_ANONYMOUS]
    )
    def test_hidden(self, api, make_user, make_game, make_platform, permission):
        user, client = make_user(
            name="badname",
            display_name="Bad Name",
            discord_id="1234",
            permissions=with_permission(permission),
        )
        play(user, make_game(), make_platform())
        hidden = f"User {user.get_id()}"

        for r in (
            api.get(f"/user/{user.get_id()}"),
            api.get(f"/user-stats/{user.get_id()}"),
            client.get("/who_am_i"),
        ):
            assert r.status_code == 200
            assert r.json()["name"] == hidden
            assert r.json()["display_name"] == hidden
            assert r.json()["discord_id"] is None

        r = api.get("/users")
        assert r.status_code == 200
        assert [u["name"] for u in r.json()] == [hidden]

    def test_not_found_by_real_name(self, api, make_user, make_game, make_platform):
        user, _ = make_user(
            name="badname", permissions=with_permission(Permission.ANONYMOUS)
        )
        play(user, make_game(), make_platform())
        assert api.get("/users", params={"search": "badname"}).json() == []
        assert api.get("/users-stats", params={"search": "badname"}).json() == []

    def test_admin_sees_everything(self, make_user):
        user, _ = make_user(
            name="badname",
            discord_id="1234",
            permissions=with_permission(Permission.FORCE_ANONYMOUS),
        )
        _, admin = make_user(name="admin", permissions=[Permission.ADMIN])
        r = admin.get(f"/admin/user/{user.get_id()}")
        assert r.status_code == 200
        assert r.json()["name"] == "badname"
        assert r.json()["discord_id"] == "1234"

    def test_avatar_shown_by_default(self, make_user, monkeypatch):
        monkeypatch.setattr(
            controller, "avatar_from_discord_user_id", lambda _: "https://real"
        )
        make_user(discord_id="1234")
        assert controller.get_avatar_url("1234") == "https://real"

    def test_unknown_avatar_not_cached(self, make_user, monkeypatch):
        cached = []
        monkeypatch.setattr(controller, "avatar_from_discord_user_id", lambda _: None)
        monkeypatch.setattr(
            controller, "cache_set", lambda *args, **kw: cached.append(args)
        )
        make_user(discord_id="1234")
        assert controller.get_avatar_url("1234") == default_avatar_url("1234")
        assert cached == []

    def test_avatar_hidden(self, make_user, monkeypatch):
        monkeypatch.setattr(
            controller, "avatar_from_discord_user_id", lambda _: "https://real"
        )
        make_user(discord_id="1234", permissions=with_permission(Permission.ANONYMOUS))
        assert controller.get_avatar_url("1234") == default_avatar_url("1234")

    def test_avatar_route_redirects_to_default(self, api, make_user):
        make_user(discord_id="1234", permissions=with_permission(Permission.ANONYMOUS))
        r = api.get("/discord/1234/avatar", allow_redirects=False)
        assert r.status_code == 307
        assert r.headers["location"] == default_avatar_url("1234")


class TestSettings:
    @pytest.mark.parametrize(
        "setting, permission",
        [
            ("anonymous", Permission.ANONYMOUS),
            ("hide_playing", Permission.HIDE_PLAYING),
            ("private", Permission.PRIVATE),
        ],
    )
    def test_on_and_off(self, make_user, setting, permission):
        user, client = make_user()
        r = client.put("/settings", json={setting: True})
        assert r.status_code == 200, r.text
        assert permission in r.json()["permissions"]
        assert User.get_by_id(user.get_id()).has_permission(permission)

        r = client.put("/settings", json={setting: False})
        assert r.status_code == 200, r.text
        assert permission not in r.json()["permissions"]

    def test_left_out_changes_nothing(self, make_user):
        user, client = make_user(permissions=with_permission(Permission.PRIVATE))
        r = client.put("/settings", json={"anonymous": True})
        assert r.status_code == 200, r.text
        assert User.get_by_id(user.get_id()).has_permission(Permission.PRIVATE)

    def test_forced_anonymous_stays(self, make_user):
        user, client = make_user(
            permissions=with_permission(Permission.FORCE_ANONYMOUS)
        )
        r = client.put("/settings", json={"anonymous": False})
        assert r.status_code == 200, r.text
        assert r.json()["name"] == f"User {user.get_id()}"
        assert Permission.FORCE_ANONYMOUS in r.json()["permissions"]


class TestHidePlaying:
    def test_left_out(self, api, make_user, make_game, make_platform):
        shown, _ = make_user(name="shown")
        hidden, hidden_client = make_user(
            name="hidden", permissions=with_permission(Permission.HIDE_PLAYING)
        )
        game = make_game()
        platform = make_platform()
        for user in (shown, hidden):
            LiveActivity.create(user=user, game=game, platform=platform, started=now())

        # not even to themselves
        for client in (api, hidden_client):
            r = client.get("/playing")
            assert r.status_code == 200, r.text
            assert [p["user_id"] for p in r.json()] == [shown.get_id()]


class TestPrivate:
    """private users are left out of everything, but their own user page"""

    @pytest.fixture
    def world(self, make_user, make_game, make_platform):
        """a public and a private user who played the same game"""
        game = make_game()
        platform = make_platform()
        public, _ = make_user(name="public")
        private, client = make_user(
            name="secret",
            display_name="Secret",
            permissions=with_permission(Permission.PRIVATE),
        )
        public_activity = play(public, game, platform, seconds=600, hours_ago=3)
        private_activity = play(private, game, platform, seconds=1000, hours_ago=1)
        return dict(
            game=game,
            platform=platform,
            public=public,
            private=private,
            client=client,
            public_activity=public_activity,
            private_activity=private_activity,
        )

    def test_own_page(self, api, world):
        uid = world["private"].get_id()
        client = world["client"]
        for path in (f"/user/{uid}", f"/user-stats/{uid}"):
            assert api.get(path).status_code == 404, path
            r = client.get(path)
            assert r.status_code == 200, path
            assert r.json()["name"] == "secret"
        assert client.get(f"/user-stats/{uid}").json()["stats"]["seconds"] == 1000

        # what the user page asks for, filtered to them
        paths = [
            ("/activities", {"user": uid}),
            ("/activity/newest", {"user": uid}),
            ("/activity/oldest", {"user": uid}),
            ("/games-stats", {"user": uid}),
            ("/platforms-stats", {"user": uid}),
            ("/charts/playtime/by_day", {"user": uid}),
            ("/total", {"users": str(uid)}),
        ]
        for path, params in paths:
            assert api.get(path, params=params).status_code == 404, path
            r = client.get(path, params=params)
            assert r.status_code == 200, path
        r = client.get("/games-stats", params={"user": uid})
        assert r.json()[0]["stats"]["seconds"] == 1000
        r = client.get("/total", params={"users": str(uid)})
        assert r.json()["seconds"] == 1000
        r = client.get("/activities", params={"user": uid})
        assert [a["id"] for a in r.json()] == [world["private_activity"].get_id()]

    def test_left_out_of_totals(self, api, world):
        game = world["game"]
        platform = world["platform"]
        # not even for themselves, only their own page has their numbers
        for client in (api, world["client"]):
            r = client.get(f"/game-stats/{game.get_id()}")
            assert r.json()["stats"]["seconds"] == 600
            assert r.json()["stats"]["user_count"] == 1
            assert r.json()["stats"]["activity_count"] == 1
            r = client.get(f"/platform-stats/{platform.get_id()}")
            assert r.json()["stats"]["seconds"] == 600
            assert r.json()["stats"]["user_count"] == 1
            r = client.get("/total")
            assert r.json()["seconds"] == 600
            assert r.json()["user_count"] == 1
            r = client.get("/total", params={"games": str(game.get_id())})
            assert r.json()["seconds"] == 600
            r = client.get("/charts/playtime/by_day", params={"game": game.get_id()})
            assert sum(sum(d["data"]) for d in r.json()["datasets"]) == 600

    def test_game_only_they_played(self, api, world, make_game):
        game = make_game("Secret Game")
        play(world["private"], game, world["platform"], hours_ago=10)
        r = api.get(f"/game-stats/{game.get_id()}")
        assert r.status_code == 200, r.text
        assert r.json()["stats"]["seconds"] == 0
        assert r.json()["stats"]["user_count"] == 0

    def test_left_out_of_lists(self, api, world):
        public_id = world["public"].get_id()
        for client in (api, world["client"]):
            r = client.get("/users", params={"limit": 100})
            assert [u["id"] for u in r.json()] == [public_id]
            r = client.get("/users-stats")
            assert [u["id"] for u in r.json()] == [public_id]
            r = client.get("/users-stats", params={"game": world["game"].get_id()})
            assert [u["id"] for u in r.json()] == [public_id]
            r = client.get("/activities")
            assert [a["id"] for a in r.json()] == [world["public_activity"].get_id()]
            r = client.get("/activity/newest")
            assert r.json()["id"] == world["public_activity"].get_id()

    def test_their_activity(self, api, world):
        aid = world["private_activity"].get_id()
        assert api.get(f"/activity/{aid}").status_code == 404
        assert world["client"].get(f"/activity/{aid}").status_code == 200
        assert api.get(f"/activities/{aid}").json() == []
        assert len(world["client"].get(f"/activities/{aid}").json()) == 1

    def test_not_found_by_id_or_search(self, api, world):
        uid = world["private"].get_id()
        public_id = world["public"].get_id()
        r = api.get(f"/users/{uid},{public_id}")
        assert [u["id"] for u in r.json()] == [public_id]
        r = api.get(f"/users-stats/{uid},{public_id}")
        assert [u["id"] for u in r.json()] == [public_id]
        assert api.get("/users", params={"search": "secret"}).json() == []

    def test_not_playing(self, api, world, make_game):
        LiveActivity.create(
            user=world["private"],
            game=make_game(),
            platform=world["platform"],
            started=now(),
        )
        assert api.get("/playing").json() == []
        assert world["client"].get("/playing").json() == []

    def test_not_in_sitemap(self, api, world):
        r = api.get("/sitemap.xml")
        assert f"/user/{world['private'].get_id()}<" not in r.text
        assert f"/user/{world['public'].get_id()}<" in r.text
