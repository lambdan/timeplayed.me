import time

import tpbackend.oblivionis.storage as oblivionis
from tpbackend.storage import Activity, Game, User
from tpbackend.permissions import Permission


def wait_for(condition, timeout=10.0):
    """
    The sync loop runs every second in the backend, so poll until it has done its thing
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.2)
    raise AssertionError("Timed out waiting for condition")


def add_oblivionis_activity(
    discord_id: str, name: str, game: str, seconds: int, platform: str = "pc"
):
    user, _ = oblivionis.User.get_or_create(id=discord_id, name=name)
    g, _ = oblivionis.Game.get_or_create(name=game)
    oblivionis.Activity.create(user=user, game=g, seconds=seconds, platform=platform)


class TestOblivionisSync:
    def test_creates_user_game_and_activity(self, api):
        add_oblivionis_activity("1234", "discordguy", "Some Game with Medal", 120)

        wait_for(lambda: oblivionis.Activity.select().count() == 0)

        user = User.get(User.discord_id == "1234")
        assert user.get_name() == "discordguy"
        # " with Medal" suffix is stripped
        game = Game.get(Game.name == "Some Game")
        activity = Activity.get(Activity.user == user)
        assert activity.get_game() == game
        assert activity.get_seconds() == 120
        # pc gets mapped to the users pc platform
        assert activity.get_platform().get_abbreviation() == "pc"
        # nobody made these, the sync did
        for model in [user, game, activity]:
            entries = model.get_history_entries()
            assert entries
            assert all(h.get_actor() is None for h in entries)

        r = api.get(f"/activity/{activity.get_id()}")
        assert r.status_code == 200
        assert r.json()["user_id"] == user.get_id()

    def test_existing_user_with_another_name(self, make_user):
        # Discord usernames can change, Oblivionis may still have the old one
        user, _ = make_user("newname", discord_id="1234")
        add_oblivionis_activity("1234", "oldname", "Some Game", 60)

        wait_for(lambda: oblivionis.Activity.select().count() == 0)

        assert User.select().count() == 1
        assert Activity.get().get_user() == user
        assert User.get_by_id(user.get_id()).get_name() == "newname"

    def test_matches_existing_game_by_alias(self, make_game):
        game = make_game("The Real Name", aliases=["Discord Name"])
        add_oblivionis_activity("1234", "discordguy", "Discord Name", 60)

        wait_for(lambda: oblivionis.Activity.select().count() == 0)

        assert Game.select().count() == 1
        assert Activity.get().get_game() == game

    def test_skips_user_without_permission(self):
        User.create(discord_id="1234", name="discordguy", permissions=[])
        add_oblivionis_activity("1234", "discordguy", "Some Game", 60)

        wait_for(lambda: oblivionis.Activity.select().count() == 0)

        assert not User.get().has_permission(Permission.DISCORD_TRACKING)
        assert Activity.select().count() == 0

    def test_drops_playstation_sessions_of_exactly_8_hours(self):
        add_oblivionis_activity("1234", "discordguy", "Capped", 28800, platform="ps5")
        add_oblivionis_activity("1234", "discordguy", "Capped too", 28800, "ps4")
        # one second off, or another platform, is a real session
        add_oblivionis_activity("1234", "discordguy", "Real", 28801, platform="ps5")
        add_oblivionis_activity("1234", "discordguy", "Real PC", 28800)

        wait_for(lambda: oblivionis.Activity.select().count() == 0)

        names = sorted(a.get_game().get_name() for a in Activity.select())
        assert names == ["Real", "Real PC"]
        # the drops are kept in the users history, to follow up on later
        history = User.get(User.discord_id == "1234").get_history()
        dropped = [h for h in history if "Dropped Oblivionis activity" in h]
        assert len(dropped) == 2
        assert "game: 'Capped', platform: 'ps5'" in dropped[0]
        assert "game: 'Capped too', platform: 'ps4'" in dropped[1]
