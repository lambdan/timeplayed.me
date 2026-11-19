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
