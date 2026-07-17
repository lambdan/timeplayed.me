import logging
import json
from tpbackend.igdb.client import IGDBClient
from tpbackend.igdb.models import IGDB_SearchResult

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
