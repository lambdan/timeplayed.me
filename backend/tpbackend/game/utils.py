from tpbackend.globals import TIMEPLAYED_URL
from tpbackend.storage import Game


def game_url(game_id) -> str:
    return f"{TIMEPLAYED_URL}/game/{game_id}"


def game_label(game: Game) -> str:
    """name with the release year if we know it, "Vice City (2002)", to tell same named games apart"""
    year = game.get_release_year()
    return f"{game.get_name()} ({year})" if year else game.get_name()


def md_game_link(game: int | Game) -> str:
    if isinstance(game, int):
        game = Game.get_by_id(game)
    assert isinstance(game, Game)
    id = game.get_id()
    name = game.get_name().strip()
    url = game_url(id)
    return f"[{name}]({url})"
