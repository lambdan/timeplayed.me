import logging
import json
from tpbackend.igdb.client import IGDBClient
from tpbackend.igdb.models import IGDB_Cover, IGDB_GameInfo, IGDB_SearchResult
from typing import cast

logger = logging.getLogger("IGDBController")
igdb = IGDBClient()

# theres a toooon of stuff: https://api-docs.igdb.com/#game


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
        cover.id
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
