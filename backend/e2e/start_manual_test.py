from discord_test import FakeAuthor, FakeMessage
from tpbackend.discord.bot import dm_receive
from tpbackend.storage import LiveActivity, User


def start(content: str) -> str:
    reply = dm_receive(FakeMessage(content, FakeAuthor()))  # type: ignore
    assert reply
    return reply


class TestStartCommand:
    def setup_method(self):
        User.create(discord_id="1234", name="discordguy")

    def test_empty(self, make_game):
        make_game("Halo")
        for content in ["!start", "!Start", "!start "]:
            assert start(content).startswith("You need to provide game ID")
        assert LiveActivity.get_or_none() is None

    def test_by_id(self, make_game):
        game = make_game("Halo")
        assert "Started playing" in start(f"!start {game.get_id()}")
        assert LiveActivity.get().get_game() == game

    def test_unknown_id(self, make_game):
        make_game("Halo")
        assert start("!start 999").startswith("Error: Game with id 999 not found")
        assert LiveActivity.get_or_none() is None

    def test_name_starting_with_a_number(self, make_game):
        # game 7 exists, but "007 First Light" is the name, not id 7
        for i in range(7):
            make_game(f"Filler {i}")
        bond = make_game("007 First Light")
        assert "Started playing" in start("!start 007 First Light")
        assert LiveActivity.get().get_game() == bond

    def test_exact_name_over_similar_ones(self, make_game):
        halo = make_game("Halo")
        make_game("Halo 2")
        make_game("Halo 3")
        assert "Started playing" in start("!start halo")
        assert LiveActivity.get().get_game() == halo

    def test_alias(self, make_game):
        game = make_game("Grand Theft Auto: San Andreas", aliases=["gtasa"])
        assert "Started playing" in start("!start gtasa")
        assert LiveActivity.get().get_game() == game

    def test_several_matches(self, make_game):
        make_game("Halo 2")
        make_game("Halo 3")
        assert start("!start halo").startswith("Not sure what game")
        assert LiveActivity.get_or_none() is None

    def test_one_match(self, make_game):
        game = make_game("Halo: Combat Evolved")
        assert "Started playing" in start("!start combat evolved")
        assert LiveActivity.get().get_game() == game

    def test_no_match(self, make_game):
        make_game("Halo")
        assert start("!start zelda") == "Error: unknown game"
