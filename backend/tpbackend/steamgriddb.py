import datetime
import os
import logging
from pydantic import BaseModel
from steamgrid import SteamGridDB
from steamgrid import StyleType, MimeType
from steamgrid.http import HTTPException


logger = logging.getLogger("SteamGridDB")
ONE_DAY = 24 * 60 * 60  # seconds
sgdb = SteamGridDB(os.environ["SGDB_TOKEN"])
cache = {}


class SGDB_Game(BaseModel):
    id: int
    name: str
    verified: bool
    release_date: datetime.datetime


class SGDB_Author(BaseModel):
    name: str
    steam64: str  # tf is this?
    avatar: str


class SGDB_Grid(BaseModel):
    id: int
    score: int
    width: int
    height: int
    style: str
    mime: str
    language: str
    url: str
    thumbnail: str
    type: str
    author: SGDB_Author
    upvotes: int
    downvotes: int


def search(query: str) -> list[SGDB_Game]:
    cacheKey = "search_" + query
    if cacheKey in cache:
        time: datetime.datetime = cache[cacheKey]["time"]
        delta = datetime.datetime.now(datetime.UTC) - time
        if delta.total_seconds() < ONE_DAY:
            logger.debug("Returning cached search result for query '%s'", query)
            return cache[cacheKey]["data"]

    s = sgdb.search_game(query)
    res = []
    if s:
        for game in s:
            if game.id and game.name and game.release_date:
                res.append(
                    SGDB_Game(
                        id=game.id,
                        name=game.name,
                        verified=bool(game.verified is not None and game.verified),
                        release_date=game.release_date,
                    )
                )

    cacheEntry = {
        "time": datetime.datetime.now(datetime.UTC),
        "data": res,
    }
    cache[cacheKey] = cacheEntry
    return res


def get_grids(game_id: int) -> list[SGDB_Grid] | None:
    cacheKey = "grids_" + str(game_id)
    if cacheKey in cache:
        time: datetime.datetime = cache[cacheKey]["time"]
        delta = datetime.datetime.now(datetime.UTC) - time
        if delta.total_seconds() < ONE_DAY:
            logger.debug("Returning cached grids for game ID %d", game_id)
            return cache[cacheKey]["data"]

    logger.debug("Fetching grids for game ID %d from SteamGridDB", game_id)

    fetch = None
    try:
        fetch = sgdb.get_grids_by_gameid(
            game_ids=[game_id],
            styles=[StyleType.Alternate],
            mimes=[MimeType.PNG, MimeType.JPEG, MimeType.WEBP],
            is_nsfw=False,
        )
    except HTTPException as e:
        logger.error("HTTPException when fetching grids for game ID %d", game_id, e)
        pass

    cache[cacheKey] = {
        "data": fetch,
        "time": datetime.datetime.now(datetime.UTC),
    }
    return fetch  # type: ignore


def get_best_grid(game_id: int) -> SGDB_Grid | None:
    grids = get_grids(game_id)
    if not grids:
        return None

    bestScore = 0
    bestGrid = None
    for grid in grids:
        thisScore = 0

        if grid.style == StyleType.Alternate:
            thisScore += 10

        if grid.language == "en":
            thisScore += 1

        if grid.width == 600 and grid.height == 900:
            thisScore += 1

        thisScore += grid.upvotes or 0
        thisScore -= grid.downvotes or 0

        if thisScore > bestScore:
            bestScore = thisScore
            bestGrid = grid

    return bestGrid
