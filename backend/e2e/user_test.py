from conftest import Api
from tpbackend.operations import add_session
from tpbackend.storage import User
from tpbackend.user.models import API_User


class TestWhoAmI:
    def test_requires_token(self, api):
        assert api.get("/who_am_i").status_code in (401, 403)

    def test_bad_token(self, make_user):
        make_user()
        assert Api("not-a-real-token").get("/who_am_i").status_code == 401

    def test_who_am_i(self, make_user):
        user, client = make_user(name="alice")
        r = client.get("/who_am_i")
        assert r.status_code == 200
        assert r.json()["id"] == user.get_id()
        assert r.json()["name"] == "alice"

    def test_has_permissions(self, make_user):
        _, client = make_user(name="alice", permissions=["commands", "admin"])
        r = client.get("/who_am_i")
        assert r.status_code == 200
        assert r.json()["permissions"] == ["commands", "admin"]


class TestNewUser:
    def test_default_platform_id_is_an_id(self):
        # a freshly created user, not loaded from the db
        user = User.create(name="new")
        assert isinstance(user.default_platform_id, int)  # type: ignore
        assert user.get_default_platform().get_abbreviation() == "unknown"
        assert API_User.from_user(user).default_platform_id == user.default_platform_id  # type: ignore

    def test_fresh_user_works_everywhere(self, make_game, make_platform):
        # how the discord bot and oblivionis sync create users, used right away
        user, created = User.get_or_create(discord_id="123", defaults={"name": "new"})
        assert created
        game = make_game()

        # add_session falls back to the default platform
        activity, error = add_session(user=user, game=game, seconds=60)
        assert error is None and activity
        assert activity.get_platform().get_abbreviation() == "unknown"

        ps5 = make_platform("ps5")
        user.set_default_platform(ps5)
        user.save()
        assert any(
            "Default platform changed from 'unknown'" in h for h in user.get_history()
        )
        assert User.get_by_id(user.get_id()).get_default_platform() == ps5
