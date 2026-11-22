import datetime

import pytest

from tpbackend import evolutions
from tpbackend.storage import Activity, History, Platform

UTC = datetime.timezone.utc
HOUR = 3600


@pytest.fixture
def family(make_user, make_game, make_platform):
    """
    PC (1h, alice)
    ├─ Windows (2h, bob)
    └─ Steam Deck (4h, alice, in 2026)
       └─ Steam Deck OLED (8h, alice, hidden activity)
    Switch (20h, alice)
    """
    alice, _ = make_user("alice")
    bob, _ = make_user("bob")
    game = make_game("Game")

    pc = make_platform("pc", name="PC")
    win = make_platform("win", name="Windows", parent=pc)
    deck = make_platform("steamdeck", name="Steam Deck", parent=pc)
    oled = make_platform("oled", name="Steam Deck OLED", parent=deck)
    switch = make_platform("switch", name="Switch")

    def add(user, platform, hours, year=2025, hidden=False):
        Activity.create(
            user=user,
            game=game,
            platform=platform,
            seconds=hours * HOUR,
            timestamp=datetime.datetime(year, 6, 1, tzinfo=UTC),
            hidden=hidden,
        )

    add(alice, pc, 1)
    add(bob, win, 2)
    add(alice, deck, 4, year=2026)
    add(alice, oled, 8, hidden=True)
    add(alice, switch, 20)

    return {
        "alice": alice,
        "game": game,
        "pc": pc,
        "win": win,
        "deck": deck,
        "switch": switch,
    }


class TestSinglePlatform:
    def test_without_children(self, api, family):
        r = api.get(f"/platform-stats/{family['pc'].get_id()}")
        assert r.status_code == 200
        assert r.json()["stats"]["seconds"] == 1 * HOUR

    def test_includes_all_depths(self, api, family):
        r = api.get(
            f"/platform-stats/{family['pc'].get_id()}",
            params={"include_child_platforms": True},
        )
        stats = r.json()["stats"]
        # hidden activity (OLED) not counted
        assert stats["seconds"] == (1 + 2 + 4) * HOUR
        assert stats["activity_count"] == 3
        assert stats["user_count"] == 2

    def test_filters_apply_to_children(self, api, family):
        r = api.get(
            f"/platform-stats/{family['pc'].get_id()}",
            params={"include_child_platforms": True, "user": family["alice"].get_id()},
        )
        assert r.json()["stats"]["seconds"] == (1 + 4) * HOUR

    def test_parent_and_children_ids(self, api, family):
        r = api.get(f"/platform/{family['pc'].get_id()}")
        assert r.json()["parent_id"] is None
        assert sorted(r.json()["children_ids"]) == sorted(
            [family["win"].get_id(), family["deck"].get_id()]
        )
        r = api.get(f"/platform/{family['win'].get_id()}")
        assert r.json()["parent_id"] == family["pc"].get_id()
        assert r.json()["children_ids"] == []


class TestPlatformList:
    def test_without_children(self, api, family):
        r = api.get("/platforms-stats")
        names = [p["display_name"] for p in r.json()]
        assert names[:4] == ["Switch", "Steam Deck", "Windows", "PC"]

    def test_children_grouped_in_parent(self, api, family):
        r = api.get("/platforms-stats", params={"include_child_platforms": True})
        platforms = [(p["display_name"], p["stats"]["seconds"]) for p in r.json()]
        assert platforms == [("Switch", 20 * HOUR), ("PC", 7 * HOUR)]


class TestPlatformFilter:
    """
    Endpoints filtering by platform, used by the platform page
    """

    def params(self, family, include):
        return {"platform": family["pc"].get_id(), "include_child_platforms": include}

    def test_games_stats(self, api, family):
        r = api.get("/games-stats", params=self.params(family, False))
        assert [g["stats"]["seconds"] for g in r.json()] == [1 * HOUR]
        r = api.get("/games-stats", params=self.params(family, True))
        assert [g["stats"]["seconds"] for g in r.json()] == [7 * HOUR]

    def test_users_stats(self, api, family):
        r = api.get("/users-stats", params=self.params(family, True))
        assert {u["name"]: u["stats"]["seconds"] for u in r.json()} == {
            "alice": 5 * HOUR,
            "bob": 2 * HOUR,
        }

    def test_activities(self, api, family):
        r = api.get("/activities", params=self.params(family, False))
        assert len(r.json()) == 1
        r = api.get("/activities", params=self.params(family, True))
        assert len(r.json()) == 3

    def test_newest_activity(self, api, family):
        r = api.get("/activity/newest", params=self.params(family, True))
        assert r.json()["platform_id"] == family["deck"].get_id()

    def test_chart(self, api, family):
        def total(include):
            r = api.get("/charts/playtime/by_day", params=self.params(family, include))
            assert r.status_code == 200
            return sum(sum(d["data"]) for d in r.json()["datasets"])

        assert total(True) > total(False)


class TestAdminParent:
    @pytest.fixture
    def client(self, make_user):
        _, client = make_user(name="admin", permissions=["admin"])
        return client

    def test_set_and_clear(self, client, make_platform):
        pc = make_platform("pc")
        mac = make_platform("mac")
        r = client.patch(
            f"/admin/platform/{mac.get_id()}", json={"parent_id": pc.get_id()}
        )
        assert r.status_code == 200, r.text
        assert r.json()["parent_id"] == pc.get_id()
        assert Platform.get_by_id(mac.get_id()).parent_id == pc.get_id()

        r = client.patch(f"/admin/platform/{mac.get_id()}", json={"parent_id": None})
        assert r.status_code == 200, r.text
        assert Platform.get_by_id(mac.get_id()).parent_id is None
        messages = [h.message for h in History.select().where(History.platform == mac)]
        assert f"Parent changed from None to 'pc' ({pc.get_id()})" in messages
        assert f"Parent changed from 'pc' ({pc.get_id()}) to None" in messages

    def test_no_loops(self, client, make_platform):
        pc = make_platform("pc")
        deck = make_platform("steamdeck", parent=pc)
        r = client.patch(
            f"/admin/platform/{pc.get_id()}", json={"parent_id": pc.get_id()}
        )
        assert r.status_code == 400
        r = client.patch(
            f"/admin/platform/{pc.get_id()}", json={"parent_id": deck.get_id()}
        )
        assert r.status_code == 400

    def test_unknown_parent(self, client, make_platform):
        pc = make_platform("pc")
        r = client.patch(f"/admin/platform/{pc.get_id()}", json={"parent_id": 9999})
        assert r.status_code == 404


class TestEvolution14:
    """puts PC operating systems and the Steam Deck under PC"""

    def test_moves_pc_platforms(self, db, make_platform):
        tp_db, _ = db
        pc = make_platform("pc", name="PC")
        moved = [make_platform(a) for a in ("win", "linux", "steamdeck")]
        switch = make_platform("switch")
        # one that already has a parent keeps it
        other = make_platform("other")
        already = make_platform("mac", parent=other)

        tp_db.cursor().execute((evolutions.EVOLUTIONS_DIR / "14.sql").read_text())

        for p in moved:
            p = Platform.get_by_id(p.get_id())
            assert p.parent_id == pc.get_id()
            assert History.select().where(History.platform == p).count() == 1
        assert Platform.get_by_id(switch.get_id()).parent_id is None
        assert Platform.get_by_id(already.get_id()).parent_id == other.get_id()
