from tpbackend.game.utils import game_url, md_game_link
from tpbackend.storage import Game


class TestMdGameLink:
    def test_includes_year(self):
        link = md_game_link(Game(id=5, name="Vice City", release_year=2002))
        assert link == f"[Vice City (2002)]({game_url(5)})"
