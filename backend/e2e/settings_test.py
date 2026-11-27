import datetime

from tpbackend.storage import Activity, User


def make_activity(user, game, platform, hidden=False) -> Activity:
    return Activity.create(
        user=user,
        game=game,
        platform=platform,
        seconds=600,
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        hidden=hidden,
    )


class TestSettings:
    def test_requires_token(self, api):
        assert api.put("/settings", json={}).status_code in (401, 403)

    def test_not_in_openapi(self, api):
        assert "/settings" not in api.get("/openapi.json").json()["paths"]

    def test_who_am_i_has_pc_platform(self, make_user):
        _, client = make_user()
        assert client.get("/who_am_i").json()["pc_platform"] == "pc"

    def test_set_pc_platform(self, make_user):
        user, client = make_user()
        r = client.put("/settings", json={"pc_platform": "linux"})
        assert r.status_code == 200
        assert r.json()["pc_platform"] == "linux"
        assert User.get_by_id(user.get_id()).get_pc_platform() == "linux"

    def test_left_out_is_unchanged(self, make_user):
        _, client = make_user()
        client.put("/settings", json={"pc_platform": "mac"})

        r = client.put("/settings", json={})
        assert r.status_code == 200
        assert r.json()["pc_platform"] == "mac"

    def test_invalid(self, make_user):
        user, client = make_user()
        assert client.put("/settings", json={"pc_platform": "amiga"}).status_code == 422
        assert User.get_by_id(user.get_id()).get_pc_platform() == "pc"

    def test_only_changes_own_user(self, make_user):
        _, alice_client = make_user("alice")
        bob, _ = make_user("bob")
        alice_client.put("/settings", json={"pc_platform": "mac"})
        assert User.get_by_id(bob.get_id()).get_pc_platform() == "pc"

    def test_nsfw_off_by_default(self, make_user):
        _, client = make_user()
        assert "show_nsfw" not in client.get("/who_am_i").json()["permissions"]

    def test_show_nsfw(self, make_user):
        user, client = make_user()
        r = client.put("/settings", json={"show_nsfw": True})
        assert r.status_code == 200
        assert "show_nsfw" in r.json()["permissions"]
        assert User.get_by_id(user.get_id()).has_permission("show_nsfw")

        # other settings leave it alone
        r = client.put("/settings", json={"pc_platform": "mac"})
        assert "show_nsfw" in r.json()["permissions"]

        r = client.put("/settings", json={"show_nsfw": False})
        assert "show_nsfw" not in r.json()["permissions"]
        assert not User.get_by_id(user.get_id()).has_permission("show_nsfw")


class TestMovePcActivity:
    def test_moves_own_pc_activity(self, make_user, make_game, make_platform):
        user, client = make_user()
        bob, _ = make_user("bob")
        pc = make_platform("pc")
        win = make_platform("win")
        ps5 = make_platform("ps5")
        game = make_game()
        mine = make_activity(user, game, pc)
        hidden = make_activity(user, game, pc, hidden=True)
        other_platform = make_activity(user, game, ps5)
        bobs = make_activity(bob, game, pc)

        r = client.put(
            "/settings", json={"pc_platform": "win", "move_pc_activity": True}
        )
        assert r.status_code == 200, r.text
        assert r.json()["pc_platform"] == "win"
        assert Activity.get_by_id(mine.get_id()).get_platform() == win
        assert Activity.get_by_id(hidden.get_id()).get_platform() == win
        assert Activity.get_by_id(other_platform.get_id()).get_platform() == ps5
        assert Activity.get_by_id(bobs.get_id()).get_platform() == pc
        assert any(
            "Platform changed from 'pc'" in h
            for h in Activity.get_by_id(mine.get_id()).get_history()
        )
        assert any(
            "Moved 2 activities (1 hidden) from 'pc' to 'win'" in h
            for h in User.get_by_id(user.get_id()).get_history()
        )

    def test_creates_missing_platform(self, make_user, make_game, make_platform):
        user, client = make_user()
        activity = make_activity(user, make_game(), make_platform("pc"))

        r = client.put(
            "/settings", json={"pc_platform": "linux", "move_pc_activity": True}
        )
        assert r.status_code == 200, r.text
        moved = Activity.get_by_id(activity.get_id()).get_platform()
        assert moved.get_abbreviation() == "linux"

    def test_not_moved_without_flag(self, make_user, make_game, make_platform):
        user, client = make_user()
        pc = make_platform("pc")
        activity = make_activity(user, make_game(), pc)

        client.put("/settings", json={"pc_platform": "win"})
        assert Activity.get_by_id(activity.get_id()).get_platform() == pc

    def test_needs_manual_activity(self, make_user, make_game, make_platform):
        user, client = make_user(permissions=[])
        pc = make_platform("pc")
        activity = make_activity(user, make_game(), pc)

        r = client.put(
            "/settings", json={"pc_platform": "win", "move_pc_activity": True}
        )
        assert r.status_code == 403
        assert Activity.get_by_id(activity.get_id()).get_platform() == pc
        # nothing changed, not even the setting
        assert User.get_by_id(user.get_id()).get_pc_platform() == "pc"

    def test_not_to_pc(self, make_user, make_game, make_platform):
        user, client = make_user()
        pc = make_platform("pc")
        activity = make_activity(user, make_game(), pc)

        r = client.put("/settings", json={"move_pc_activity": True})
        assert r.status_code == 400
        assert Activity.get_by_id(activity.get_id()).get_platform() == pc
