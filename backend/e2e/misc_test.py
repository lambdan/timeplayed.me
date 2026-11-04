class TestPing:
    def test_ping(self, api):
        r = api.get("/ping")
        assert r.status_code == 200
        assert r.json() == "pong"
