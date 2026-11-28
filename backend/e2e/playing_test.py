import datetime

import pytest

from tpbackend.permissions import DEFAULT_PERMISSIONS, Permission
from tpbackend.storage import Activity, DiscordPresence, LiveActivity, User
from tpbackend.utils2 import dt_to_ts, now


def minutes_ago(n: float) -> datetime.datetime:
    return now() - datetime.timedelta(minutes=n)


def ts(dt: datetime.datetime) -> int:
    return dt_to_ts(dt)


def presence(discord_user_id: str, game_name: str, platform: str, **kwargs):
    defaults = dict(
        discord_user_name="someone",
        started=minutes_ago(30),
        last_seen=minutes_ago(1),
    )
    return DiscordPresence.create(
        discord_user_id=discord_user_id,
        game_name=game_name,
        platform=platform,
        **(defaults | kwargs),
    )


@pytest.fixture
def ps5(make_platform):
    return make_platform("ps5")


class TestPlaying:
    def test_nothing(self, api):
        r = api.get("/playing")
        assert r.status_code == 200, r.text
        assert r.json() == []

    def test_manual(self, api, make_user, make_game, ps5):
        user, _ = make_user(permissions=DEFAULT_PERMISSIONS)
        game = make_game()
        started = minutes_ago(10)
        LiveActivity.create(user=user, game=game, platform=ps5, started=started)

        r = api.get("/playing")
        assert r.status_code == 200, r.text
        assert r.json() == [
            {
                "user_id": user.get_id(),
                "game_id": game.get_id(),
                "platform_id": ps5.get_id(),
                "started": ts(started),
                "source": "manual",
            }
        ]

    def test_manual_without_permission(self, api, make_user, make_game, ps5):
        user, _ = make_user(permissions=[])
        LiveActivity.create(
            user=user, game=make_game(), platform=ps5, started=minutes_ago(10)
        )
        assert api.get("/playing").json() == []

    def test_discord(self, api, make_user, make_game, ps5):
        user, _ = make_user(discord_id="555", permissions=DEFAULT_PERMISSIONS)
        game = make_game("Some Game")
        discord_started = minutes_ago(40)
        presence("555", "Some Game", "ps5", discord_started=discord_started)

        [playing] = api.get("/playing").json()
        assert playing["user_id"] == user.get_id()
        assert playing["game_id"] == game.get_id()
        assert playing["platform_id"] == ps5.get_id()
        # Discord's start is earlier than when the bot first saw them
        assert playing["started"] == ts(discord_started)
        assert playing["source"] == "discord"

    def test_discord_mapped_like_the_sync(
        self, api, make_user, make_game, make_platform
    ):
        make_user(
            discord_id="555", permissions=DEFAULT_PERMISSIONS, pc_platform="linux"
        )
        game = make_game("Some Game", aliases=["Some Game Beta"])
        linux = make_platform("linux")
        presence("555", "Some Game Beta with Medal", "pc")

        [playing] = api.get("/playing").json()
        assert playing["game_id"] == game.get_id()
        assert playing["platform_id"] == linux.get_id()

    def test_discord_skipped(self, api, make_user, make_game, ps5):
        make_user(name="a", discord_id="1", permissions=DEFAULT_PERMISSIONS)
        make_user(name="b", discord_id="2", permissions=[])
        make_game("Known")
        make_game("Hidden", hidden=True)
        # game not created yet
        presence("1", "Unknown", "ps5")
        # platform not created yet
        presence("1", "Known", "switch2")
        # hidden game
        presence("1", "Hidden", "ps5")
        # not seen for a while, the bot was down
        presence("1", "Known", "ps5", last_seen=minutes_ago(10))
        # no oblivionis_sync
        presence("2", "Known", "ps5")
        # no user yet
        presence("3", "Known", "ps5")

        assert api.get("/playing").json() == []

    def test_child_of_hidden_game_is_skipped(self, api, make_user, make_game, ps5):
        user, _ = make_user(permissions=DEFAULT_PERMISSIONS)
        parent = make_game("Parent", hidden=True)
        child = make_game("Child", parent=parent)
        LiveActivity.create(
            user=user, game=child, platform=ps5, started=minutes_ago(10)
        )
        assert api.get("/playing").json() == []

    def test_manual_and_discord_is_listed_once(self, api, make_user, make_game, ps5):
        user, _ = make_user(discord_id="555", permissions=DEFAULT_PERMISSIONS)
        game = make_game("Some Game")
        LiveActivity.create(user=user, game=game, platform=ps5, started=minutes_ago(10))
        presence("555", "Some Game", "ps5", started=minutes_ago(20))

        [playing] = api.get("/playing").json()
        assert playing["started"] == ts(DiscordPresence.get().get_started())
        assert playing["source"] == "discord"

    def test_newest_first(self, api, make_user, make_game, ps5):
        alice, _ = make_user(name="alice", permissions=DEFAULT_PERMISSIONS)
        bob, _ = make_user(name="bob", permissions=DEFAULT_PERMISSIONS)
        game = make_game()
        LiveActivity.create(
            user=alice, game=game, platform=ps5, started=minutes_ago(60)
        )
        LiveActivity.create(user=bob, game=game, platform=ps5, started=minutes_ago(5))

        r = api.get("/playing")
        assert [p["user_id"] for p in r.json()] == [bob.get_id(), alice.get_id()]

    def test_one_user(self, api, make_user, make_game, ps5):
        alice, _ = make_user(name="alice")
        bob, _ = make_user(name="bob")
        game = make_game()
        for user in (alice, bob):
            LiveActivity.create(user=user, game=game, platform=ps5, started=now())

        r = api.get("/playing", params={"user": bob.get_id()})
        assert r.status_code == 200, r.text
        assert [p["user_id"] for p in r.json()] == [bob.get_id()]


class TestAdminLive:
    def test_list(self, make_user, make_game, ps5):
        _, admin = make_user(name="admin", permissions=["admin"])
        user, _ = make_user(name="alice", permissions=[])
        game = make_game("Some Game")
        started = minutes_ago(10)
        live = LiveActivity.create(user=user, game=game, platform=ps5, started=started)

        r = admin.get("/admin/live")
        assert r.status_code == 200, r.text
        assert r.json() == [
            {
                "id": live.get_id(),
                "user_id": user.get_id(),
                "user_name": "alice",
                "game_id": game.get_id(),
                "game_name": "Some Game",
                "platform_id": ps5.get_id(),
                "platform_abbreviation": "ps5",
                "started": ts(started),
                # can't stop it
                "manual_activity": False,
            }
        ]

    def test_requires_admin(self, make_user):
        _, client = make_user(name="regular")
        assert client.get("/admin/live").status_code == 403

    def test_discard(self, make_user, make_game, ps5):
        admin_user, admin = make_user(name="admin", permissions=["admin"])
        user, _ = make_user(name="alice")
        live = LiveActivity.create(
            user=user,
            game=make_game("Echo"),
            platform=ps5,
            started=datetime.datetime(2026, 7, 30, 2, 16, tzinfo=datetime.UTC),
        )

        r = admin.delete(f"/admin/live/{live.get_id()}")
        assert r.status_code == 200, r.text
        assert LiveActivity.select().count() == 0
        # nothing stored
        assert Activity.select().count() == 0
        [entry] = User.get_by_id(user.get_id()).get_history_entries()
        assert entry.get_actor() == admin_user
        assert (
            entry.message
            == "Manual tracking discarded by admin (game: 'Echo', platform: 'ps5', started: 2026-07-30T02:16:00Z)"
        )

    def test_discard_missing(self, make_user):
        _, admin = make_user(name="admin", permissions=["admin"])
        assert admin.delete("/admin/live/123").status_code == 404
