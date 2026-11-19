import datetime

from tpbackend.storage import Activity

UTC = datetime.timezone.utc


def make_activity(user, game, platform, hidden=False) -> Activity:
    return Activity.create(
        user=user,
        game=game,
        platform=platform,
        seconds=600,
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=UTC),
        hidden=hidden,
    )


class TestSetActivityPlatform:
    def test_own_activity(self, make_user, make_game, make_platform):
        user, client = make_user()
        ps4 = make_platform("ps4")
        ps5 = make_platform("ps5")
        activity = make_activity(user, make_game(), ps4)

        r = client.put(
            f"/activity/{activity.get_id()}/platform",
            json={"platform_id": ps5.get_id()},
        )
        assert r.status_code == 200, r.text
        assert r.json()["platform_id"] == ps5.get_id()
        changed = Activity.get_by_id(activity.get_id())
        assert changed.get_platform() == ps5
        assert any("Platform changed from 'ps4'" in h for h in changed.get_history())

    def test_hidden_activity(self, make_user, make_game, make_platform):
        user, client = make_user()
        ps5 = make_platform("ps5")
        activity = make_activity(user, make_game(), make_platform("ps4"), hidden=True)
        r = client.put(
            f"/activity/{activity.get_id()}/platform",
            json={"platform_id": ps5.get_id()},
        )
        assert r.status_code == 200, r.text

    def test_someone_elses_activity(self, make_user, make_game, make_platform):
        alice, _ = make_user("alice")
        _, bob = make_user("bob")
        ps4 = make_platform("ps4")
        activity = make_activity(alice, make_game(), ps4)

        r = bob.put(
            f"/activity/{activity.get_id()}/platform",
            json={"platform_id": make_platform("ps5").get_id()},
        )
        assert r.status_code == 403
        assert Activity.get_by_id(activity.get_id()).get_platform() == ps4

    def test_not_found(self, make_user, make_game, make_platform):
        user, client = make_user()
        activity = make_activity(user, make_game(), make_platform("ps4"))
        r = client.put("/activity/999/platform", json={"platform_id": 1})
        assert r.status_code == 404
        r = client.put(
            f"/activity/{activity.get_id()}/platform", json={"platform_id": 999}
        )
        assert r.status_code == 404

    def test_requires_token(self, api, make_user, make_game, make_platform):
        user, _ = make_user()
        activity = make_activity(user, make_game(), make_platform("ps4"))
        r = api.put(f"/activity/{activity.get_id()}/platform", json={"platform_id": 1})
        assert r.status_code in (401, 403)


class TestEditPermission:
    def test_requires_manual_activity(self, make_user, make_game, make_platform):
        # everything but manual_activity
        user, client = make_user(permissions=["commands", "oblivionis_sync"])
        old = make_game("Old")
        ps4 = make_platform("ps4")
        activity = make_activity(user, old, ps4)
        path = f"/activity/{activity.get_id()}"

        r = client.put(f"{path}/game", json={"game_id": make_game("New").get_id()})
        assert r.status_code == 403
        r = client.put(
            f"{path}/platform", json={"platform_id": make_platform("ps5").get_id()}
        )
        assert r.status_code == 403

        unchanged = Activity.get_by_id(activity.get_id())
        assert unchanged.get_game() == old
        assert unchanged.get_platform() == ps4

        # deleting can't inflate anything, so it needs no permission
        assert client.delete(path).status_code == 200


class TestSetActivityGame:
    def test_own_activity(self, make_user, make_game, make_platform):
        user, client = make_user()
        emulator = make_game("RetroArch")
        game = make_game("Super Mario World")
        activity = make_activity(user, emulator, make_platform())

        r = client.put(
            f"/activity/{activity.get_id()}/game", json={"game_id": game.get_id()}
        )
        assert r.status_code == 200, r.text
        assert r.json()["game_id"] == game.get_id()
        changed = Activity.get_by_id(activity.get_id())
        assert changed.get_game() == game
        assert any("Game changed from 'RetroArch'" in h for h in changed.get_history())

    def test_someone_elses_activity(self, make_user, make_game, make_platform):
        alice, _ = make_user("alice")
        _, bob = make_user("bob")
        old = make_game("Old")
        activity = make_activity(alice, old, make_platform())

        r = bob.put(
            f"/activity/{activity.get_id()}/game",
            json={"game_id": make_game("New").get_id()},
        )
        assert r.status_code == 403
        assert Activity.get_by_id(activity.get_id()).get_game() == old

    def test_not_found(self, make_user, make_game, make_platform):
        user, client = make_user()
        old = make_game("Old")
        activity = make_activity(user, old, make_platform())

        r = client.put("/activity/999/game", json={"game_id": old.get_id()})
        assert r.status_code == 404
        r = client.put(f"/activity/{activity.get_id()}/game", json={"game_id": 999})
        assert r.status_code == 404
        assert Activity.get_by_id(activity.get_id()).get_game() == old

    def test_hidden_game(self, make_user, make_game, make_platform):
        user, client = make_user()
        activity = make_activity(user, make_game(), make_platform())
        hidden = make_game("Hidden", hidden=True)
        r = client.put(
            f"/activity/{activity.get_id()}/game", json={"game_id": hidden.get_id()}
        )
        assert r.status_code == 200, r.text

    def test_requires_token(self, api, make_user, make_game, make_platform):
        user, _ = make_user()
        activity = make_activity(user, make_game(), make_platform())
        r = api.put(f"/activity/{activity.get_id()}/game", json={"game_id": 1})
        assert r.status_code in (401, 403)
