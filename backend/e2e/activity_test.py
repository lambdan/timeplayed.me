import pytest
import datetime

from tpbackend import utils2
from tpbackend.operations import add_session
from tpbackend.storage import Activity, Platform


@pytest.fixture
def platform_id(make_platform):
    """the api requires a platform"""
    return make_platform("testplatform").get_id()


class TestAddActivity:
    def test_add_and_get(self, make_user, make_game, make_platform, api):
        user, client = make_user()
        game = make_game()
        platform = make_platform()

        r = client.post(
            "/activity",
            json={
                "game_id": game.get_id(),
                "platform_id": platform.get_id(),
                "seconds": 3600,
            },
        )
        assert r.status_code == 200, r.text
        added = r.json()
        assert added["user_id"] == user.get_id()
        assert added["game_id"] == game.get_id()
        assert added["platform_id"] == platform.get_id()
        assert added["seconds"] == 3600
        assert added["ended"] - added["started"] == 3600 * 1000

        # readable by anyone
        r = api.get(f"/activity/{added['id']}")
        assert r.status_code == 200
        assert r.json() == added

        # history should say where it came from
        activity = Activity.get_by_id(added["id"])
        assert any("Activity source: API" in h for h in activity.get_history())

    def test_requires_auth(self, api, make_game, platform_id):
        game = make_game()
        r = api.post(
            "/activity",
            json={"platform_id": platform_id, "game_id": game.get_id(), "seconds": 60},
        )
        assert r.status_code in (401, 403)
        assert Activity.select().count() == 0

    def test_requires_platform(self, make_user, make_game):
        _, client = make_user()
        game = make_game()

        r = client.post("/activity", json={"game_id": game.get_id(), "seconds": 60})
        assert r.status_code == 422, r.text
        assert "platform_id" in r.text
        assert Activity.select().count() == 0

    def test_unknown_game(self, make_user, platform_id):
        _, client = make_user()
        r = client.post(
            "/activity",
            json={"platform_id": platform_id, "game_id": 999, "seconds": 60},
        )
        assert r.status_code == 404

    def test_no_game(self, make_user, platform_id):
        _, client = make_user()
        r = client.post("/activity", json={"platform_id": platform_id, "seconds": 60})
        assert r.status_code == 400

    def test_zero_seconds(self, make_user, make_game, platform_id):
        _, client = make_user()
        game = make_game()
        r = client.post(
            "/activity",
            json={"platform_id": platform_id, "game_id": game.get_id(), "seconds": 0},
        )
        assert r.status_code == 422

    def test_overlapping_activity_is_merged(self, make_user, make_game, platform_id):
        _, client = make_user()
        game = make_game()

        first = client.post(
            "/activity",
            json={"platform_id": platform_id, "game_id": game.get_id(), "seconds": 60},
        )
        assert first.status_code == 200, first.text
        first_activity = Activity.get_by_id(first.json()["id"])
        first_activity.add_history("where the first one came from")
        first_activity.save()
        # second session "ended" just now and was longer, so it covers the first one
        second = client.post(
            "/activity",
            json={"platform_id": platform_id, "game_id": game.get_id(), "seconds": 600},
        )
        assert second.status_code == 200, second.text

        assert Activity.select().count() == 1
        assert second.json()["seconds"] >= 600
        # the first one is extended, and keeps its history
        assert second.json()["id"] == first.json()["id"]
        history = Activity.get_by_id(first.json()["id"]).get_history()
        assert any(
            "Merged in an overlapping session (600 seconds" in h for h in history
        )
        assert any("where the first one came from" in h for h in history)

    def test_all_overlapping_activities_are_merged(
        self, make_user, make_game, platform_id
    ):
        user, client = make_user()
        game = make_game()

        # three short sessions over the last hour, not overlapping each other
        now = utils2.now()
        short_ids = []
        for minutes_ago in [50, 30, 10]:
            short, err = add_session(
                user=user,
                game=game,
                seconds=60,
                platform=Platform.get_by_id(platform_id),
                timestamp=now - datetime.timedelta(minutes=minutes_ago),
            )
            assert err is None
            short_ids.append(short.get_id())
        assert Activity.select().count() == 3

        # one long session ending now that covers all of them
        long = client.post(
            "/activity",
            json={
                "platform_id": platform_id,
                "game_id": game.get_id(),
                "seconds": 3600,
            },
        )
        assert long.status_code == 200, long.text

        assert Activity.select().count() == 1
        assert long.json()["seconds"] >= 3600
        # one of the short ones is extended, the others are merged into it
        kept_id = long.json()["id"]
        assert kept_id in short_ids
        history = Activity.get_by_id(kept_id).get_history()
        assert any(
            "Merged in an overlapping session (3600 seconds" in h for h in history
        )
        for short_id in short_ids:
            if short_id != kept_id:
                assert any(f"overlapped activity id {short_id}" in h for h in history)

    def test_non_overlapping_activity_is_kept(self, make_user, make_game, platform_id):
        user, client = make_user()
        game = make_game()

        _, err = add_session(
            user=user,
            game=game,
            seconds=60,
            platform=Platform.get_by_id(platform_id),
            timestamp=utils2.now() - datetime.timedelta(hours=2),
        )
        assert err is None
        r = client.post(
            "/activity",
            json={"platform_id": platform_id, "game_id": game.get_id(), "seconds": 600},
        )
        assert r.status_code == 200, r.text

        assert Activity.select().count() == 2


class TestDeleteActivity:
    def test_delete_own(self, make_user, make_game, api, platform_id):
        _, client = make_user()
        game = make_game()
        added = client.post(
            "/activity",
            json={"platform_id": platform_id, "game_id": game.get_id(), "seconds": 60},
        ).json()

        r = client.delete(f"/activity/{added['id']}")
        assert r.status_code == 200
        assert api.get(f"/activity/{added['id']}").status_code == 404

    def test_cannot_delete_others(self, make_user, make_game, platform_id):
        _, alice = make_user(name="alice")
        _, bob = make_user(name="bob")
        game = make_game()
        added = alice.post(
            "/activity",
            json={"platform_id": platform_id, "game_id": game.get_id(), "seconds": 60},
        ).json()

        r = bob.delete(f"/activity/{added['id']}")
        assert r.status_code == 403
        assert Activity.select().count() == 1


class TestLiveActivity:
    def test_requires_platform(self, make_user, make_game):
        _, client = make_user()
        game = make_game()
        r = client.post("/activity/live", json={"game_id": game.get_id()})
        assert r.status_code == 422, r.text
        assert "platform_id" in r.text

    def test_start_and_abort(self, make_user, make_game, platform_id):
        user, client = make_user()
        game = make_game()

        r = client.post(
            "/activity/live",
            json={"platform_id": platform_id, "game_id": game.get_id()},
        )
        assert r.status_code == 200, r.text
        assert r.json()["game_id"] == game.get_id()

        # can't have two at once
        r = client.post(
            "/activity/live",
            json={"platform_id": platform_id, "game_id": game.get_id()},
        )
        assert r.status_code == 400

        assert client.get("/activity/live").json()["user_id"] == user.get_id()
        assert client.delete("/activity/live").status_code == 200
        assert client.get("/activity/live").status_code == 404
        assert Activity.select().count() == 0

    def test_stop_creates_activity(self, make_user, make_game, platform_id):
        _, client = make_user()
        game = make_game()

        assert (
            client.post(
                "/activity/live",
                json={"platform_id": platform_id, "game_id": game.get_id()},
            ).status_code
            == 200
        )
        r = client.post("/activity/live/stop")
        # MINIMUM_SESSION_LENGTH is 0 in the e2e env, so even an instant session is saved
        assert r.status_code == 200, r.text
        assert r.json()["game_id"] == game.get_id()
        assert client.get("/activity/live").status_code == 404


class TestManualActivityPermission:
    def test_requires_permission(self, make_user, make_game, platform_id):
        # everything but manual_activity
        _, client = make_user(permissions=["commands", "discord_tracking"])
        game = make_game()

        r = client.post(
            "/activity",
            json={"platform_id": platform_id, "game_id": game.get_id(), "seconds": 60},
        )
        assert r.status_code == 403
        r = client.post(
            "/activity/live",
            json={"platform_id": platform_id, "game_id": game.get_id()},
        )
        assert r.status_code == 403
        assert client.get("/activity/live").status_code == 403
        assert client.post("/activity/live/stop").status_code == 403
        assert client.delete("/activity/live").status_code == 403
        assert Activity.select().count() == 0
