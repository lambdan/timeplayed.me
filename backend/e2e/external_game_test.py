from tpbackend.operations import adopt_name
from tpbackend.storage import Game


class TestAdoptName:
    def test_same_name(self, make_game):
        game = make_game("Vice City")
        assert adopt_name(game, "Vice City", "IGDB") == ("", False)

    def test_renames_and_keeps_old_as_alias(self, make_game):
        game = make_game("GTA VC")
        out, conflict = adopt_name(game, "Grand Theft Auto: Vice City", "IGDB")
        assert not conflict
        assert "Replaced name with IGDB name" in out
        assert game.get_name() == "Grand Theft Auto: Vice City"
        assert "GTA VC" in game.get_aliases()

    def test_name_is_alias_swaps(self, make_game):
        # eg set a wrong IGDB ID and then the right one again
        game = make_game("Wrong Game", aliases=["Vice City"])
        out, conflict = adopt_name(game, "Vice City", "IGDB")
        assert not conflict
        assert game.get_name() == "Vice City"
        assert game.get_aliases() == ["Wrong Game"]

    def test_other_game_has_the_name(self, make_game):
        make_game("Grand Theft Auto: Vice City")
        game = make_game("GTA VC")
        out, conflict = adopt_name(game, "Grand Theft Auto: Vice City", "SGDB")
        assert conflict
        assert "OTHER GAME HAS SGDB NAME" in out
        assert Game.get_by_id(game.get_id()).get_name() == "GTA VC"
