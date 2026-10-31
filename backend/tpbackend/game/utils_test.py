from tpbackend.game.utils import game_label
from tpbackend.storage import Game


class TestGameLabel:
    def test_with_year(self):
        assert (
            game_label(Game(name="Vice City", release_year=2002)) == "Vice City (2002)"
        )

    def test_without_year(self):
        assert game_label(Game(name="Vice City")) == "Vice City"
