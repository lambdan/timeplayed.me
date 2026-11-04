class TestWhoAmI:
    def test_has_permissions(self, make_user):
        _, client = make_user(name="alice", permissions=["commands", "admin"])
        r = client.get("/who_am_i")
        assert r.status_code == 200
        assert r.json()["permissions"] == ["commands", "admin"]
