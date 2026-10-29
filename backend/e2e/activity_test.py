from conftest import Api
from tpbackend.storage import Activity


class TestAuth:
    def test_ping(self, api):
        r = api.get("/ping")
        assert r.status_code == 200
        assert r.json() == "pong"

    def test_who_am_i_requires_token(self, api):
        assert api.get("/who_am_i").status_code in (401, 403)

    def test_who_am_i_bad_token(self, make_user):
        make_user()
        assert Api("not-a-real-token").get("/who_am_i").status_code == 401

    def test_who_am_i(self, make_user):
        user, client = make_user(name="alice")
        r = client.get("/who_am_i")
        assert r.status_code == 200
        assert r.json()["id"] == user.get_id()
        assert r.json()["name"] == "alice"


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

    def test_requires_auth(self, api, make_game):
        game = make_game()
        r = api.post("/activity", json={"game_id": game.get_id(), "seconds": 60})
        assert r.status_code in (401, 403)
        assert Activity.select().count() == 0

    def test_uses_default_platform(self, make_user, make_game, make_platform):
        platform = make_platform("switch")
        user, client = make_user(default_platform=platform)
        game = make_game()

        r = client.post("/activity", json={"game_id": game.get_id(), "seconds": 60})
        assert r.status_code == 200, r.text
        assert r.json()["platform_id"] == platform.get_id()

    def test_unknown_game(self, make_user):
        _, client = make_user()
        r = client.post("/activity", json={"game_id": 999, "seconds": 60})
        assert r.status_code == 404

    def test_no_game(self, make_user):
        _, client = make_user()
        r = client.post("/activity", json={"seconds": 60})
        assert r.status_code == 400

    def test_zero_seconds(self, make_user, make_game):
        _, client = make_user()
        game = make_game()
        r = client.post("/activity", json={"game_id": game.get_id(), "seconds": 0})
        assert r.status_code == 422

    def test_overlapping_activity_is_merged(self, make_user, make_game):
        _, client = make_user()
        game = make_game()

        first = client.post("/activity", json={"game_id": game.get_id(), "seconds": 60})
        assert first.status_code == 200, first.text
        # second session "ended" just now and was longer, so it covers the first one
        second = client.post(
            "/activity", json={"game_id": game.get_id(), "seconds": 600}
        )
        assert second.status_code == 200, second.text

        assert Activity.select().count() == 1
        assert second.json()["seconds"] >= 600
        activity = Activity.get_by_id(second.json()["id"])
        assert any(
            f"overlapped activity id {first.json()['id']}" in h
            for h in activity.get_history()
        )


class TestDeleteActivity:
    def test_delete_own(self, make_user, make_game, api):
        _, client = make_user()
        game = make_game()
        added = client.post(
            "/activity", json={"game_id": game.get_id(), "seconds": 60}
        ).json()

        r = client.delete(f"/activity/{added['id']}")
        assert r.status_code == 200
        assert api.get(f"/activity/{added['id']}").status_code == 404

    def test_cannot_delete_others(self, make_user, make_game):
        _, alice = make_user(name="alice")
        _, bob = make_user(name="bob")
        game = make_game()
        added = alice.post(
            "/activity", json={"game_id": game.get_id(), "seconds": 60}
        ).json()

        r = bob.delete(f"/activity/{added['id']}")
        assert r.status_code == 403
        assert Activity.select().count() == 1


class TestLiveActivity:
    def test_start_and_abort(self, make_user, make_game):
        user, client = make_user()
        game = make_game()

        r = client.post("/activity/live", json={"game_id": game.get_id()})
        assert r.status_code == 200, r.text
        assert r.json()["game_id"] == game.get_id()

        # can't have two at once
        r = client.post("/activity/live", json={"game_id": game.get_id()})
        assert r.status_code == 400

        assert client.get("/activity/live").json()["user_id"] == user.get_id()
        assert client.delete("/activity/live").status_code == 200
        assert client.get("/activity/live").status_code == 404
        assert Activity.select().count() == 0

    def test_stop_creates_activity(self, make_user, make_game):
        _, client = make_user()
        game = make_game()

        assert (
            client.post("/activity/live", json={"game_id": game.get_id()}).status_code
            == 200
        )
        r = client.post("/activity/live/stop")
        # MINIMUM_SESSION_LENGTH is 0 in the e2e env, so even an instant session is saved
        assert r.status_code == 200, r.text
        assert r.json()["game_id"] == game.get_id()
        assert client.get("/activity/live").status_code == 404
