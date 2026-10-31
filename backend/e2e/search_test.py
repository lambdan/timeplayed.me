from discord_test import FakeAuthor, FakeMessage
from tpbackend.discord.bot import dm_receive
from tpbackend.storage import User


class TestSearchCommand:
    def test_same_named_games_show_year(self, make_game):
        User.create(discord_id="1234", name="discordguy", permissions=["commands"])
        make_game("Vice City", release_year=2002)
        make_game("Vice City", release_year=2026)
        make_game("Vice City Stories")

        reply = dm_receive(FakeMessage("!search vice city", FakeAuthor()))  # type: ignore
        assert reply
        assert "[Vice City (2002)]" in reply
        assert "[Vice City (2026)]" in reply
        assert "[Vice City Stories]" in reply
