import datetime

from tpbackend.storage import Activity

UTC = datetime.timezone.utc


def ids(response):
    assert response.status_code == 200
    return [row["id"] for row in response.json()]


class TestSort:
    def test_games_nulls_last_both_ways(self, api, make_game):
        old = make_game("Old", release_year=2002)
        new = make_game("New", release_year=2026)
        unknown = make_game("Unknown")

        r = api.get("/games", params={"sort": "release_year", "order": "asc"})
        assert ids(r) == [old.get_id(), new.get_id(), unknown.get_id()]
        r = api.get("/games", params={"sort": "release_year", "order": "desc"})
        assert ids(r) == [new.get_id(), old.get_id(), unknown.get_id()]

    def test_games_stats_by_playtime(self, api, make_user, make_game, make_platform):
        user, _ = make_user()
        pc = make_platform("pc")
        short = make_game("Short")
        long = make_game("Long")
        now = datetime.datetime.now(UTC)
        Activity.create(user=user, game=short, platform=pc, seconds=60, timestamp=now)
        Activity.create(user=user, game=long, platform=pc, seconds=6000, timestamp=now)

        r = api.get("/games-stats", params={"sort": "playtime", "order": "desc"})
        assert ids(r) == [long.get_id(), short.get_id()]
        r = api.get("/games-stats", params={"sort": "playtime", "order": "asc"})
        assert ids(r) == [short.get_id(), long.get_id()]

    def test_activities_by_timestamp(self, api, make_user, make_game, make_platform):
        user, _ = make_user()
        pc = make_platform("pc")
        game = make_game()
        now = datetime.datetime.now(UTC)
        older = Activity.create(
            user=user,
            game=game,
            platform=pc,
            seconds=60,
            timestamp=now - datetime.timedelta(days=1),
        )
        newer = Activity.create(
            user=user, game=game, platform=pc, seconds=60, timestamp=now
        )

        r = api.get("/activities", params={"order": "desc"})
        assert ids(r) == [newer.get_id(), older.get_id()]
        r = api.get("/activities", params={"order": "asc"})
        assert ids(r) == [older.get_id(), newer.get_id()]
