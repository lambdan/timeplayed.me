import logging
import json
from tpbackend.game.query import GameQuery
from tpbackend.game.select import GameSelect
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
    res = igdb.request(url="https://api.igdb.com/v4/games", query=data)
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
    res = igdb.request(url="https://api.igdb.com/v4/games", query=data)
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

    game = GameSelect.by_igdb_id(igdb_game_id)
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


def get_or_create_game_by_steam_id(
    steam_app_id: int, history_create_msg: str
) -> Game | None:
    if not steam_app_id:
        return None

    game = GameSelect.by_steam_id(steam_app_id)
    if game:
        return game

    # look it up on igdb
    # external source 1 = steam
    data = f"""
    fields uid, name, game; 
    where uid = "{steam_app_id}" & external_game_source = 1; 
    limit 1;
    """

    res = igdb.request(url="https://api.igdb.com/v4/external_games", query=data)
    logger.info("Got res: %s", res)
    igdb_game_id = None
    if res:
        try:
            parsed = json.loads(res)
            # id = ???
            # game = igdb id
            # name = game name on igdb
            # uid = steam app id
            igdb_game_id = int(parsed[0]["game"])
        except Exception as e:
            logger.error("Error parsing IGDB external game response: %s", e)
            igdb_game_id = None

    if not igdb_game_id:
        return None

    created_game = get_or_create_game(igdb_game_id, history_create_msg)
    if not created_game:
        return None

    # update internal game with steam id
    created_game.set_steam_id(steam_app_id)
    created_game.save()

    return created_game
