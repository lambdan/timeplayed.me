import logging
import json
from tpbackend.igdb.client import IGDBClient
from tpbackend.igdb.models import IGDB_SearchResult
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
            ret.append(
                IGDB_SearchResult(
                    id=r.get("id"),
                    first_release_date=r.get("first_release_date", None),
                    name=r.get("name"),
                    url=r.get("url"),
                )
            )
    return ret


def get_cover_for_game(
    igdb_game_id: int, size="t_cover_big", format="png"
) -> str | None:
    data = f"fields cover.image_id; where id = {igdb_game_id};"
    res = igdb.request(data, cache_expiry=86400)
    logger.info("Got res: %s", res)
    try:
        parsed = json.loads(cast(str, res))
        cover = parsed[0].get("cover", None)
        image_id = cover.get("image_id", None)
        if image_id:
            return (
                f"https://images.igdb.com/igdb/image/upload/{size}/{image_id}.{format}"
            )
    except Exception as e:
        logger.error("Error parsing IGDB cover response: %s", e)
    return None
