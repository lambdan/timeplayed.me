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


def add_oblivionis_activity(discord_id: str, name: str, game: str, seconds: int):
    user, _ = oblivionis.User.get_or_create(id=discord_id, name=name)
    g, _ = oblivionis.Game.get_or_create(name=game)
    oblivionis.Activity.create(user=user, game=g, seconds=seconds, platform="pc")


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
        assert activity.get_platform().get_abbreviation() == "win"

        r = api.get(f"/activity/{activity.get_id()}")
        assert r.status_code == 200
        assert r.json()["user_id"] == user.get_id()

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

        assert not User.get().has_permission(Permission.OBLIVIONIS_SYNC)
        assert Activity.select().count() == 0
