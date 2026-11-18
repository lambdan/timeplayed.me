import datetime

import pytest

from tpbackend.storage import Activity

UTC = datetime.timezone.utc
HOUR = 3600


@pytest.fixture
def family(make_user, make_game, make_platform):
    """
    GTA V (1h, alice)
    ├─ GTA V Enhanced (2h, bob)
    └─ FiveM (4h, alice)
       └─ STRP (8h, alice, in 2026)
          └─ STRP EU (16h, bob, hidden activity)
    Other game (20h, alice)
    """
    alice, _ = make_user("alice")
    bob, _ = make_user("bob")
    platform = make_platform()

    gta = make_game("GTA V")
    enhanced = make_game("GTA V Enhanced", parent=gta)
    fivem = make_game("FiveM", parent=gta)
    strp = make_game("STRP", parent=fivem)
    strp_eu = make_game("STRP EU", parent=strp)
    other = make_game("Other game")

    def add(user, game, hours, year=2025, hidden=False):
        Activity.create(
            user=user,
            game=game,
            platform=platform,
            seconds=hours * HOUR,
            timestamp=datetime.datetime(year, 6, 1, tzinfo=UTC),
            hidden=hidden,
        )

    add(alice, gta, 1)
    add(bob, enhanced, 2)
    add(alice, fivem, 4)
    add(alice, strp, 8, year=2026)
    add(bob, strp_eu, 16, hidden=True)
    add(alice, other, 20)

    return {
        "alice": alice,
        "gta": gta,
        "fivem": fivem,
        "strp": strp,
        "other": other,
    }


class TestSingleGame:
    def test_without_children(self, api, family):
        r = api.get(f"/game-stats/{family['gta'].get_id()}")
        assert r.status_code == 200
        assert r.json()["stats"]["seconds"] == 1 * HOUR

    def test_includes_all_depths(self, api, family):
        r = api.get(
            f"/game-stats/{family['gta'].get_id()}", params={"include_children": True}
        )
        stats = r.json()["stats"]
        # hidden activity (STRP EU) not counted
        assert stats["seconds"] == (1 + 2 + 4 + 8) * HOUR
        assert stats["activity_count"] == 4
        # alice and bob, each counted once
        assert stats["user_count"] == 2

    def test_child_includes_its_own_children(self, api, family):
        r = api.get(
            f"/game-stats/{family['fivem'].get_id()}", params={"include_children": True}
        )
        assert r.json()["stats"]["seconds"] == (4 + 8) * HOUR

    def test_filters_apply_to_children(self, api, family):
        gta_id = family["gta"].get_id()
        r = api.get(
            f"/game-stats/{gta_id}",
            params={"include_children": True, "user": family["alice"].get_id()},
        )
        assert r.json()["stats"]["seconds"] == (1 + 4 + 8) * HOUR

        after = int(datetime.datetime(2026, 1, 1, tzinfo=UTC).timestamp() * 1000)
        r = api.get(
            f"/game-stats/{gta_id}", params={"include_children": True, "after": after}
        )
        assert r.json()["stats"]["seconds"] == 8 * HOUR


class TestManyGames:
    def test_children_can_be_requested(self, api, family):
        ids = f"{family['gta'].get_id()},{family['fivem'].get_id()}"
        r = api.get(f"/games-stats/{ids}", params={"include_children": True})
        seconds = {g["name"]: g["stats"]["seconds"] for g in r.json()}
        assert seconds == {"GTA V": 15 * HOUR, "FiveM": 12 * HOUR}


class TestGameList:
    def test_without_children(self, api, family):
        r = api.get("/games-stats")
        names = [g["name"] for g in r.json()]
        # STRP EU only has a hidden activity, so no playtime
        assert names == [
            "Other game",
            "STRP",
            "FiveM",
            "GTA V Enhanced",
            "GTA V",
            "STRP EU",
        ]

    def test_children_grouped_in_parent(self, api, family):
        r = api.get("/games-stats", params={"include_children": True})
        games = [(g["name"], g["stats"]["seconds"]) for g in r.json()]
        assert games == [("Other game", 20 * HOUR), ("GTA V", 15 * HOUR)]


class TestGameFilter:
    """
    Endpoints filtering by game, used by the game page
    """

    def params(self, family, include_children):
        return {"game": family["gta"].get_id(), "include_children": include_children}

    def test_users_stats(self, api, family):
        r = api.get("/users-stats", params=self.params(family, False))
        assert {u["name"]: u["stats"]["seconds"] for u in r.json()} == {
            "alice": 1 * HOUR
        }

        r = api.get("/users-stats", params=self.params(family, True))
        assert {u["name"]: u["stats"]["seconds"] for u in r.json()} == {
            "alice": (1 + 4 + 8) * HOUR,
            "bob": 2 * HOUR,
        }

    def test_platforms_stats(self, api, family):
        r = api.get("/platforms-stats", params=self.params(family, True))
        assert [p["stats"]["seconds"] for p in r.json()] == [15 * HOUR]

    def test_activities(self, api, family):
        r = api.get("/activities", params=self.params(family, False))
        assert len(r.json()) == 1

        r = api.get("/activities", params=self.params(family, True))
        # hidden STRP EU activity not included
        assert len(r.json()) == 4

    def test_newest_activity(self, api, family):
        r = api.get("/activity/newest", params=self.params(family, True))
        assert r.json()["game_id"] == family["strp"].get_id()

    def test_chart(self, api, family):
        r = api.get("/charts/playtime/by_day", params=self.params(family, True))
        assert r.status_code == 200
        total = sum(sum(d["data"]) for d in r.json()["datasets"])
        assert total > sum(
            sum(d["data"])
            for d in api.get(
                "/charts/playtime/by_day", params=self.params(family, False)
            ).json()["datasets"]
        )


def test_include_children_false_is_false(api, family):
    r = api.get(
        f"/game-stats/{family['gta'].get_id()}", params={"include_children": "false"}
    )
    assert r.json()["stats"]["seconds"] == 1 * HOUR
