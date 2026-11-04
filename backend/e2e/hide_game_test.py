import datetime

from discord_test import FakeAuthor, FakeMessage
from tpbackend.discord.bot import dm_receive
from tpbackend.storage import Activity, Game, User

UTC = datetime.timezone.utc


class TestHideGameCommand:
    def test_toggles_game_and_activities(self, make_game, make_platform):
        user = User.create(
            discord_id="1234",
            name="discordguy",
            permissions=["commands", "admin"],
        )
        game = make_game()
        Activity.create(
            user=user,
            game=game,
            platform=make_platform(),
            seconds=3600,
            timestamp=datetime.datetime.now(UTC),
        )
        cmd = f"!hide_game {game.get_id()}"

        reply = dm_receive(FakeMessage(cmd, FakeAuthor()))  # type: ignore
        assert reply and "is now hidden. 1 activities" in reply
        assert Game.get_by_id(game.get_id()).get_hidden() is True
        assert Activity.get().get_hidden() is True

        reply = dm_receive(FakeMessage(cmd, FakeAuthor()))  # type: ignore
        assert reply and "is now visible. 1 activities" in reply
        assert Game.get_by_id(game.get_id()).get_hidden() is False
        assert Activity.get().get_hidden() is False
