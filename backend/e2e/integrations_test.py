"""
The e2e env runs without Discord, SGDB and IGDB credentials, so these check that the
backend behaves when they are disabled.
"""


class TestSGDBDisabled:
    def test_grids_unavailable(self, api):
        assert api.get("/sgdb/1/grids").status_code == 503
        assert api.get("/sgdb/1/grids/best").status_code == 503


class TestIGDBDisabled:
    def test_game_info_unavailable(self, api):
        assert api.get("/igdb/game/1").status_code == 503

    def test_game_by_igdb_id_not_in_db(self, api):
        assert api.get("/game_igdb/1234").status_code == 503

    def test_game_by_igdb_id_in_db(self, api, make_game):
        game = make_game(igdb_id=1234)
        r = api.get("/game_igdb/1234")
        assert r.status_code == 200
        assert r.json()["id"] == game.get_id()

    def test_add_activity_by_unknown_igdb_id(self, make_user):
        _, client = make_user()
        r = client.post("/activity", json={"igdb_id": 1234, "seconds": 60})
        assert r.status_code == 503

    def test_add_activity_by_unknown_steam_id(self, make_user):
        _, client = make_user()
        r = client.post("/activity", json={"steam_id": 1234, "seconds": 60})
        assert r.status_code == 503

    def test_add_activity_by_known_ids(self, make_user, make_game):
        _, client = make_user()
        by_igdb = make_game("IGDB game", igdb_id=1234)
        by_steam = make_game("Steam game", steam_id=5678)

        r = client.post("/activity", json={"igdb_id": 1234, "seconds": 60})
        assert r.status_code == 200, r.text
        assert r.json()["game_id"] == by_igdb.get_id()

        r = client.post("/activity", json={"steam_id": 5678, "seconds": 60})
        assert r.status_code == 200, r.text
        assert r.json()["game_id"] == by_steam.get_id()

    def test_start_live_activity_by_unknown_igdb_id(self, make_user):
        _, client = make_user()
        r = client.post("/activity/live", json={"igdb_id": 1234})
        assert r.status_code == 503


class TestDiscordDisabled:
    def test_avatar_falls_back_to_default(self, api):
        r = api.get("/discord/1234/avatar", allow_redirects=False)
        assert r.status_code == 307
        assert r.headers["location"] == "https://cdn.discordapp.com/embed/avatars/4.png"
