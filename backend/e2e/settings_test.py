from conftest import Api
from tpbackend.storage import User


class TestSettings:
    def test_requires_token(self, api):
        assert api.put("/settings", json={}).status_code in (401, 403)

    def test_who_am_i_has_pc_platform(self, make_user):
        _, client = make_user()
        assert client.get("/who_am_i").json()["pc_platform"] == "win"

    def test_set_default_platform(self, make_user, make_platform):
        user, client = make_user()
        ps5 = make_platform("ps5")

        r = client.put("/settings", json={"default_platform_id": ps5.get_id()})
        assert r.status_code == 200
        assert r.json()["default_platform_id"] == ps5.get_id()
        assert (
            User.get_by_id(user.get_id()).get_default_platform().get_id()
            == ps5.get_id()
        )

    def test_set_pc_platform(self, make_user):
        user, client = make_user()
        r = client.put("/settings", json={"pc_platform": "linux"})
        assert r.status_code == 200
        assert r.json()["pc_platform"] == "linux"
        assert User.get_by_id(user.get_id()).get_pc_platform() == "linux"

    def test_left_out_is_unchanged(self, make_user, make_platform):
        user, client = make_user()
        ps5 = make_platform("ps5")
        client.put("/settings", json={"default_platform_id": ps5.get_id()})

        r = client.put("/settings", json={"pc_platform": "mac"})
        assert r.json()["default_platform_id"] == ps5.get_id()
        assert r.json()["pc_platform"] == "mac"

    def test_invalid(self, make_user):
        user, client = make_user()
        assert (
            client.put("/settings", json={"default_platform_id": 999}).status_code
            == 400
        )
        assert client.put("/settings", json={"pc_platform": "amiga"}).status_code == 422
        assert User.get_by_id(user.get_id()).get_pc_platform() == "win"

    def test_only_changes_own_user(self, make_user, make_platform):
        alice, alice_client = make_user("alice")
        bob, _ = make_user("bob")
        alice_client.put("/settings", json={"pc_platform": "mac"})
        assert User.get_by_id(bob.get_id()).get_pc_platform() == "win"
