from tpbackend.discord import controller
from tpbackend.discord.bot import default_avatar_url
from tpbackend.operations import add_session
from tpbackend.permissions import DEFAULT_PERMISSIONS, Permission


def permissions_without(permission: Permission) -> list[str]:
    return [p for p in DEFAULT_PERMISSIONS if p != permission]


class TestHideName:
    def test_name_shown_by_default(self, api, make_user):
        user, _ = make_user(name="alice", display_name="Alice")
        r = api.get(f"/user/{user.get_id()}")
        assert r.status_code == 200
        assert r.json()["name"] == "alice"
        assert r.json()["display_name"] == "Alice"

    def test_name_hidden(self, api, make_user, make_game):
        user, client = make_user(
            name="badname",
            display_name="Bad Name",
            permissions=permissions_without(Permission.SHOW_NAME),
        )
        add_session(user=user, game=make_game(), seconds=60)
        hidden = f"User {user.get_id()}"

        for r in (
            api.get(f"/user/{user.get_id()}"),
            api.get(f"/user-stats/{user.get_id()}"),
            client.get("/who_am_i"),
        ):
            assert r.status_code == 200
            assert r.json()["name"] == hidden
            assert r.json()["display_name"] == hidden

        r = api.get("/users")
        assert r.status_code == 200
        assert [u["name"] for u in r.json()] == [hidden]

    def test_admin_sees_real_name(self, make_user):
        user, _ = make_user(
            name="badname", permissions=permissions_without(Permission.SHOW_NAME)
        )
        _, admin = make_user(name="admin", permissions=[Permission.ADMIN])
        r = admin.get(f"/admin/user/{user.get_id()}")
        assert r.status_code == 200
        assert r.json()["name"] == "badname"


class TestHideAvatar:
    def test_avatar_shown_by_default(self, make_user, monkeypatch):
        monkeypatch.setattr(
            controller, "avatar_from_discord_user_id", lambda _: "https://real"
        )
        make_user(discord_id="1234")
        assert controller.get_avatar_url("1234") == "https://real"

    def test_avatar_hidden(self, make_user, monkeypatch):
        monkeypatch.setattr(
            controller, "avatar_from_discord_user_id", lambda _: "https://real"
        )
        make_user(
            discord_id="1234", permissions=permissions_without(Permission.SHOW_AVATAR)
        )
        assert controller.get_avatar_url("1234") == default_avatar_url("1234")

    def test_avatar_route_redirects_to_default(self, api, make_user):
        make_user(
            discord_id="1234", permissions=permissions_without(Permission.SHOW_AVATAR)
        )
        r = api.get("/discord/1234/avatar", allow_redirects=False)
        assert r.status_code == 307
        assert r.headers["location"] == default_avatar_url("1234")
