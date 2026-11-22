from tpbackend.storage import User


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
