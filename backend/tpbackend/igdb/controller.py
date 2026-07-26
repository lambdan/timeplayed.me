import logging
import json
from tpbackend.game.query import GameQuery
from tpbackend.igdb.client import IGDBClient
from tpbackend.igdb.models import IGDB_Cover, IGDB_GameInfo, IGDB_SearchResult
from typing import cast

from tpbackend.storage import Game
from tpbackend.utils2 import ts_to_dt

logger = logging.getLogger("IGDBController")
igdb = IGDBClient()

# theres a toooon of stuff: https://api-docs.igdb.com/#game


def available() -> bool:
    return igdb.available()


def search_game(query: str) -> list[IGDB_SearchResult]:
    data = f'search "{query}"; fields id,name,first_release_date,url; limit 10;'
    res = igdb.request(data)
    logger.info("Got res: %s", res)
    ret = []
    if res:
        for r in json.loads(res):
            ret.append(IGDB_SearchResult.model_validate(r))
    return ret


def get_game_info(igdb_game_id: int) -> IGDB_GameInfo | None:
    # bleh, this is kind of a mess...
    data = f"""
    fields id,
        involved_companies,
        platforms,
        name,
        first_release_date,url,
        summary,
        cover.image_id,
        cover.id,
        similar_games,
        expanded_games, expansions, parent_game, ports, remakes, remasters, standalone_expansions
        ; 
    where id = {igdb_game_id};
    """
    # to get everything:
    # data = f"fields *; where id = {igdb_game_id};"
    res = igdb.request(data)
    logger.info("Got res: %s", res)
    try:
        parsed = json.loads(cast(str, res))
        if parsed:
            return IGDB_GameInfo.model_validate(parsed[0])
    except Exception as e:
        logger.error("Error parsing IGDB game info response: %s", e)
    return None


def get_or_create_game(igdb_game_id: int, history_create_msg: str) -> Game | None:
    if not igdb_game_id:
        return None

    game = Game.get_or_none(Game.igdb_id == igdb_game_id)
    if game:
        return game

    igdb_game = get_game_info(igdb_game_id)
    if not igdb_game:
        return None

    game_year = None
    if igdb_game.first_release_date:
        dt = ts_to_dt(igdb_game.first_release_date)
        game_year = dt.year

    new_game = Game.create(
        name=igdb_game.name, igdb_id=igdb_game_id, release_year=game_year
    )
    new_game = cast(Game, new_game)
    new_game.add_history(history_create_msg)
    new_game.save()
    return new_game
